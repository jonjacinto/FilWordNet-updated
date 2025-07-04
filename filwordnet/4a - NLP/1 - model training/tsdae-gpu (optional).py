import time
import torch
import pandas as pd
import nltk # required sa training
nltk.download('punkt') # required sa training
from sentence_transformers.datasets import DenoisingAutoEncoderDataset
from torch.utils.data import DataLoader
from sentence_transformers import models, SentenceTransformer
from sentence_transformers.losses import DenoisingAutoEncoderLoss
import wandb


def process_data():
    print("PROCESSING DATA...")
    MODEL_DIR = r"D:/thesis/corpus/COHFIE_V1"

    DATA_READER = pd.read_csv(f'{MODEL_DIR}/COHFIE_TRAINING.csv', chunksize=500000)

    sentences = []
    count = 0
    for DATA in DATA_READER:
        sentences += DATA.loc[DATA['source'] != 'wikipedia'].text.str.replace(r"(?<!\S)XX_[A-Za-z]*(?!\S)", "").str.replace(r" \?", "?").str.replace(r" ,", ",").str.replace(r" !", "!").str.replace(r"\.\.\.", "").str.replace(r" \.$", ".").str.replace(r"\(.*?\)", ".").str.replace(r'\"', "").str.strip().tolist()
        count += 1
        print(count)

    sentences = list(set(sentences))
    print(f"NUMBER OF SENTENCES: {len(sentences)}")
    
    return sentences


if __name__ == "__main__":
    print(f"GPU: {torch.cuda.is_available()}")
    
    sentences = process_data()

    # dataset class with noise functionality built-in
    train_data = DenoisingAutoEncoderDataset(sentences)

    # we use a dataloader as usual
    loader = DataLoader(train_data, batch_size=32, shuffle=True, drop_last=True)

    roberta = models.Transformer(fr"D:/thesis/model/roberta-tagalog-base-cased-finetuned-epoch10", max_seq_length=64)

    pooler = models.Pooling(
        roberta.get_word_embedding_dimension(),
        pooling_mode='cls'
    )

    model = SentenceTransformer(modules=[roberta, pooler])


    loss = DenoisingAutoEncoderLoss(model, tie_encoder_decoder=True)

    # INIT WANDB
    wandb.init(project="filwordnet", entity="danvelasco")

    save_steps = len(loader) // 3
    model.fit(
        train_objectives=[(loader, loss)],
        epochs=1,
        weight_decay=0,
        scheduler='constantlr',
        optimizer_params={'lr': 3e-5},
        output_path='./finetunedMLM-sroberta-tsdae',
        show_progress_bar=True,
        use_amp=True,
        checkpoint_path='./finetunedMLM-sroberta-tsdae-chkpnt',
        checkpoint_save_steps=save_steps,
        checkpoint_save_total_limit=0
    )