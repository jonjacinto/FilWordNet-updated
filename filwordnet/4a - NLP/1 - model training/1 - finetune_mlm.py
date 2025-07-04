import math
import wandb
import torch_xla
import torch_xla.core.xla_model as xm
from transformers import TFAutoModel, AutoModelForMaskedLM, AutoTokenizer, TrainingArguments, Trainer, DataCollatorForLanguageModeling
from transformers.optimization import AdamW, get_linear_schedule_with_warmup
from datasets import load_dataset

def tokenize_function(examples):
    return tokenizer(examples["text"])

def group_texts(examples):
    # set block size
    block_size = 32

    # Concatenate all texts.
    concatenated_examples = {k: sum(examples[k], []) for k in examples.keys()}
    total_length = len(concatenated_examples[list(examples.keys())[0]])
    # We drop the small remainder, we could add padding if the model supported it instead of this drop, you can
    # customize this part to your needs.
    total_length = (total_length // block_size) * block_size
    # Split by chunks of max_len.
    result = {
        k: [t[i : i + block_size] for i in range(0, total_length, block_size)]
        for k, t in concatenated_examples.items()
    }
    result["labels"] = result["input_ids"].copy()
    return result

def model_init(mode="TPU"):
    model = AutoModelForMaskedLM.from_pretrained('jcblaise/roberta-tagalog-base', output_hidden_states=True, return_dict=True)
    model.resize_token_embeddings(len(tokenizer))

    if mode == "TPU":
        device = xm.xla_device()
        model = model.to(device)
    
    return model

if __name__ == "__main__":
    # Instantiate tokenzier
    repo = 'jcblaise/roberta-tagalog-base'
    print(f"Downloading tokenizer from: {repo}")
    tokenizer = AutoTokenizer.from_pretrained(repo, return_token_type_ids=False)
    device = xm.xla_device()
    print(f"device: {device}") # if ok, it prints xla:1

    # Prepare data

    ## Load dataset
    data_files = ['COHFIE_LITE.csv']
    print(f"Loading {data_files}...")
    dataset = load_dataset('csv', data_files=data_files)

    ## train-test split
    test_size = 0.2
    shuffle = True
    seed = 27
    print(f"Train-Test split: {1-test_size}-{test_size}")
    print(f"shuffle: {shuffle}")
    print(f"seed: {seed}")
    dataset = dataset['train'].train_test_split(test_size=test_size, shuffle=shuffle, seed=seed)

    ## Add special tokens
    special_tokens_dict = {'additional_special_tokens': ['XX_EMOJI', 'XX_URL', 'XX_EMAIL', 'XX_USERNAME', 'XX_HASHTAG', 'XX_SEQSAMESYMBOLS', 'XX_SEQNOTSAMESYMBOLS']}
    print(f"Adding special tokens: {special_tokens_dict}")
    tokenizer.add_special_tokens(special_tokens_dict)

    print("Tokenizing texts...")
    tokenized_dataset = dataset.map(tokenize_function, batched=True, num_proc=4, remove_columns=['text', 'pos_tags', 'lang', 'lang_prob', 'source', 'source_type', 'year', 'month'])

    print("Grouping texts....")
    lm_dataset = tokenized_dataset.map(group_texts, batched=True, batch_size=1000, num_proc=4,)
    del tokenized_dataset # delete tokenized_dataset

    # responsible for masking for each epoch
    data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm_probability=0.15)

    # train
    ## Initialize wandb
    wandb.init(project="filwordnet", entity="danvelasco")

    ## Set training arguments
    training_args = TrainingArguments(
        f"roberta-base-cased-test",
        evaluation_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=5,
        per_device_train_batch_size=64,
        per_device_eval_batch_size=64,
        logging_steps=500,
        num_train_epochs=10,
    )

    ## Initialize pretrained model
    model = model_init()

    ## Setup Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=lm_dataset['train'],
        eval_dataset=lm_dataset['test'],
        data_collator=data_collator)

    print(f"place_model_on_device: {trainer.place_model_on_device}")
    print(f"train_batch_size: {trainer.args.train_batch_size}")

    ## Execute training
    trainer.train()

    # Evaluate 
    eval_results = trainer.evaluate()
    print(f"Perplexity: {math.exp(eval_results['eval_loss']):.2f}")