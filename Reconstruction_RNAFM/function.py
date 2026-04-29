# This script is used to reconstruct the RNA sequence using the RNA-FM model
# including the following functions:
# 1.create embedding for the RNA sequence
# 2. secondary structure prediction for the RNA sequence
# 3. rna family classification for the RNA sequence
# 4. mRNA expression level prediction for the RNA sequence

import os
import glob
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from Bio import SeqIO
from sklearn.manifold import TSNE
from sklearn.model_selection import train_test_split
try:
    from tqdm.notebook import tqdm
except ImportError:
    from tqdm import tqdm

import fm  # RNA-FM package

### 1. Embedding and Secondary Structure Prediction

class RNAFMEmbedder:
    def __init__(self, model_type="ss", model_path=None, device=None):
        if device is None:
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.device = device
        if model_type == "ss":
            self.model, self.alphabet = fm.downstream.build_rnafm_resnet(type="ss")
        elif model_type == "rna":
            self.model, self.alphabet = fm.pretrained.rna_fm_t12(model_path)
        elif model_type == "mrna":
            self.model, self.alphabet = fm.pretrained.mrna_fm_t12()
        else:
            raise ValueError("Unknown RNAFM model type.")
        self.batch_converter = self.alphabet.get_batch_converter()
        self.model.to(self.device)
        self.model.eval()

    def embed_sequences(self, seq_tuples, repr_layer=12, mean_pool=False, batch_size=16):
        all_embeddings = []
        with torch.no_grad():
            for i in tqdm(range(0, len(seq_tuples), batch_size), desc='Embedding sequences'):
                batch = seq_tuples[i:i + batch_size]
                batch_labels, batch_strs, batch_tokens = self.batch_converter(batch)
                results = self.model(batch_tokens.to(self.device), repr_layers=[repr_layer])
                emb = results["representations"][repr_layer].cpu().numpy()
                if mean_pool and len(emb.shape) == 3:
                    emb = emb.mean(axis=1)
                all_embeddings.append(emb)
        if len(all_embeddings) == 0:
            return np.array([])
        if all_embeddings[0].ndim == 2:  # mean pooled
            return np.concatenate(all_embeddings, axis=0)
        else:
            return np.concatenate(all_embeddings, axis=0)  # (N, L, d)

    def predict_secondary_structure(self, seq_list):
        # Expects seq_list: [("seqid", "sequence"), ...]
        batch_labels, batch_strs, batch_tokens = self.batch_converter(seq_list)
        # 将 tokens 移动到正确的设备
        batch_tokens = batch_tokens.to(self.device)
        input_dict = {
            "description": batch_labels,
            "token": batch_tokens
        }
        with torch.no_grad():
            results = self.model(input_dict)
        ss_prob_map = results["r-ss"]
        return ss_prob_map

### 2. RNA Family Clustering

def load_fasta_folder_as_tuples(fasta_folder):
    fasta_paths = sorted(glob.glob(os.path.join(fasta_folder, 'RF*.fasta')))
    seqs, labels = [], []
    rfam_list = []
    for fasta_path in fasta_paths:
        rfam = Path(fasta_path).stem
        rfam_list.append(rfam)
        records = list(SeqIO.parse(fasta_path, 'fasta'))
        fasta_seqs = [str(record.seq) for record in records]
        fasta_seq_names = [record.id for record in records]
        seqs += [(seq_name, seq) for seq_name, seq in zip(fasta_seq_names, fasta_seqs)]
        labels += [rfam] * len(fasta_seq_names)
    return seqs, labels, rfam_list

def postprocess_ss_prob_map(prob_map, seq, threshold=0.5, allow_nc=True):
    """
    后处理二级结构概率图，去除多重配对（multiplets）和过滤非标准配对
    
    参数:
        prob_map: 二级结构概率图，numpy array 形状为 (L, L)
        seq: RNA 序列字符串
        threshold: 配对概率阈值
        allow_nc: 是否允许非标准配对（non-canonical pairs）
    
    返回:
        pred_map: 完整配对图（包含多重配对）
        pred_map_without_multiplets: 去除多重配对的配对图
        multiplet_list: 多重配对列表
    """
    canonical_pairs = ['AU', 'UA', 'GC', 'CG', 'GU', 'UG']
    
    # 去除对角线（自己和自己配对）
    prob_map = prob_map * (1 - np.eye(prob_map.shape[0]))
    pred_map = (prob_map > threshold)
    
    # 去除多重配对：当多个配对冲突时，选择概率最高的
    seq_len = len(seq)
    x_array, y_array = np.nonzero(pred_map)
    prob_array = []
    for i in range(x_array.shape[0]):
        prob_array.append(prob_map[x_array[i], y_array[i]])
    prob_array = np.array(prob_array)
    
    sort_index = np.argsort(-prob_array)  # 按概率降序排序
    
    mask_map = np.zeros_like(pred_map)
    already_x = set()
    already_y = set()
    multiplet_list = []
    
    for index in sort_index:
        x = x_array[index]
        y = y_array[index]
        
        # 不允许太短的环（<=1个碱基）
        if abs(x - y) <= 1:
            continue
        
        # 检查是否是标准配对
        seq_pair = seq[x] + seq[y]
        if seq_pair not in canonical_pairs and allow_nc == False:
            continue
        
        # 如果冲突（已经配对），记录为多重配对
        if x in already_x or y in already_y:
            multiplet_list.append([x+1, y+1])
            continue
        else:
            mask_map[x, y] = 1
            already_x.add(x)
            already_y.add(y)
    
    pred_map_without_multiplets = pred_map * mask_map
    
    return pred_map, pred_map_without_multiplets, multiplet_list


def matrix2ct(prob_map, seq, seq_id, output_path, threshold=0.5, allow_nc=True):
    """
    将二级结构概率图转换为 .ct 格式文件
    
    参数:
        prob_map: 二级结构概率图，numpy array 或 tensor，形状为 (L, L)
        seq: RNA 序列字符串
        seq_id: 序列ID
        output_path: 输出 .ct 文件路径
        threshold: 配对概率阈值
        allow_nc: 是否允许非标准配对
    """
    import numpy as np
    
    # 转换为 numpy array
    if hasattr(prob_map, 'cpu'):
        prob_map = prob_map.cpu().numpy()
    elif hasattr(prob_map, 'numpy'):
        prob_map = prob_map.numpy()
    
    # 如果是批次，取第一个
    if len(prob_map.shape) == 3:
        prob_map = prob_map[0]
    
    # 后处理：去除多重配对
    _, contact, _ = postprocess_ss_prob_map(prob_map, seq, threshold=threshold, allow_nc=allow_nc)
    
    # 写入 .ct 文件
    seq_len = len(seq)
    structure = np.where(contact)
    pair_dict = dict()
    for i in range(seq_len):
        pair_dict[i] = -1
    for i in range(len(structure[0])):
        pair_dict[structure[0][i]] = structure[1][i]
    
    first_col = list(range(1, seq_len+1))  # 位置（从1开始）
    second_col = list(seq)  # 碱基
    third_col = list(range(seq_len))  # 前一个位置（从0开始）
    fourth_col = list(range(2, seq_len+2))  # 后一个位置（从2开始）
    fifth_col = [pair_dict[i]+1 for i in range(seq_len)]  # 配对位置（0表示未配对）
    last_col = list(range(1, seq_len+1))  # 配对状态（位置本身）
    
    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, "w") as f:
        f.write("{}\t{}\n".format(seq_len, seq_id))  # 第一行：序列长度和ID
        for i in range(seq_len):
            f.write("{}\t{}\t{}\t{}\t{}\t{}\n".format(
                first_col[i], second_col[i], third_col[i], 
                fourth_col[i], fifth_col[i], last_col[i]
            ))


def plot_secondary_structure(ss_prob_map, sequence_id="seq_0", output_path=None, figsize=(10, 8)):
    """
    可视化二级结构概率图
    
    参数:
        ss_prob_map: 二级结构概率图，形状为 (L, L) 或 (N, L, L) 的 tensor
        sequence_id: 序列ID（用于标题）
        output_path: 输出图片路径，如果为 None 则显示图片
        figsize: 图片大小
    """
    import matplotlib.pyplot as plt
    import numpy as np
    
    # 如果是批次，取第一个
    if len(ss_prob_map.shape) == 3:
        ss_prob = ss_prob_map[0].cpu().numpy() if hasattr(ss_prob_map, 'cpu') else ss_prob_map[0]
    else:
        ss_prob = ss_prob_map.cpu().numpy() if hasattr(ss_prob_map, 'cpu') else ss_prob_map
    
    plt.figure(figsize=figsize)
    plt.imshow(ss_prob, cmap='viridis', aspect='auto')
    plt.colorbar(label='Probability')
    plt.title(f'Secondary Structure Probability Map - {sequence_id}')
    plt.xlabel('Position j')
    plt.ylabel('Position i')
    
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"二级结构可视化图片已保存到: {output_path}")
    else:
        plt.show()
    plt.close()


def plot_tsne_embeddings(embeddings, labels, label_to_name=None, colors=None, figsize=(8,8), output_path=None):
    unique_labels = sorted(set(labels))
    plt.figure(figsize=figsize)
    if colors is None:
        import matplotlib
        color_list = list(matplotlib.colors.TABLEAU_COLORS.values()) + ['C'+str(i) for i in range(10)]
        colors = color_list[:len(unique_labels)]
    for idx, label in enumerate(unique_labels):
        indices = [i for i, l in enumerate(labels) if l == label]
        label_disp = label_to_name[label] if label_to_name and label in label_to_name else label
        plt.scatter(embeddings[indices, 0], embeddings[indices, 1], color=colors[idx], s=5, alpha=0.5, label=label_disp)
    plt.legend()
    plt.xticks([])
    plt.yticks([])
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"图片已保存到: {output_path}")
    else:
        plt.show()
    plt.close()

def perform_tsne(embeddings, n_components=2, random_state=42):
    tsne = TSNE(n_components=n_components, random_state=random_state)
    return tsne.fit_transform(embeddings)

### 3. RNA Family Classification

class RNATypeDataset(Dataset):
    def __init__(self, embeddings, labels, mean_pool=False):
        self.embeddings = embeddings
        self.labels = labels
        self.mean_pool = mean_pool

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        emb = self.embeddings[idx]
        if self.mean_pool and emb.ndim == 2:
            emb = np.mean(emb, axis=0)
        return emb, self.labels[idx]

class RNATypeClassifier(nn.Module):
    def __init__(self, in_dim, num_class):
        super().__init__()
        self.fc = nn.Linear(in_dim, num_class)

    def forward(self, x):
        return self.fc(x)

def train_classifier(model, train_loader, val_loader, test_loader, device, num_epochs=100, lr=1e-3, checkpoint_path='rna_type_checkpoint.pt', display_step=20, output_path=None):
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    max_val_acc = -1
    best_epoch = -1
    train_loss_history = []
    val_loss_history = []
    train_acc_history = []
    val_acc_history = []

    for epoch in tqdm(range(num_epochs), desc="Training classifier"):
        model.train()
        train_losses, train_preds, train_targets = [], [], []
        for x, y in train_loader:
            x, y = x.to(device).float(), y.to(device).long()
            y_pred = model(x)
            loss = criterion(y_pred, y)
            train_losses.append(loss.item())
            train_preds.append(torch.max(y_pred.detach(), 1)[1])
            train_targets.append(y)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

        model.eval()
        val_losses, val_preds, val_targets = [], [], []
        for x, y in val_loader:
            x, y = x.to(device).float(), y.to(device).long()
            y_pred = model(x)
            loss = criterion(y_pred, y)
            val_losses.append(loss.item())
            val_preds.append(torch.max(y_pred.detach(), 1)[1])
            val_targets.append(y)

        train_preds = torch.cat(train_preds, dim=0)
        train_targets = torch.cat(train_targets, dim=0)
        train_acc = (train_preds == train_targets).float().mean().cpu()

        val_preds = torch.cat(val_preds, dim=0)
        val_targets = torch.cat(val_targets, dim=0)
        val_acc = (val_preds == val_targets).float().mean().cpu()

        train_acc_history.append(train_acc)
        val_acc_history.append(val_acc)
        train_loss_history.append(np.mean(train_losses))
        val_loss_history.append(np.mean(val_losses))

        # Save checkpoint if validation improves
        if val_acc > max_val_acc:
            torch.save({'model_state_dict': model.state_dict()}, checkpoint_path)
            best_epoch = epoch
            max_val_acc = val_acc

        if display_step and epoch % display_step == 1:
            print(f'epoch {epoch}/{num_epochs}: train loss={np.mean(train_losses):.6f}, train acc={train_acc:.6f}, val loss={np.mean(val_losses):.6f}, val acc={val_acc:.6f}')

    # Plot loss & accuracy history
    loss_output = os.path.join(output_path, "loss_history.png") if output_path else None
    acc_output = os.path.join(output_path, "accuracy_history.png") if output_path else None
    _plot_training_history(train_loss_history, val_loss_history, best_epoch, "Loss History", ylabel="Loss", output_path=loss_output)
    _plot_training_history(train_acc_history, val_acc_history, best_epoch, "Accuracy History", ylabel="Accuracy", output_path=acc_output)

    # Test
    model.load_state_dict(torch.load(checkpoint_path)['model_state_dict'])
    model.eval()
    test_preds = []
    y_test_full = []
    for x, y in test_loader:
        x = x.to(device).float()
        output = model(x)
        _, y_pred = torch.max(output.data, 1)
        test_preds.append(y_pred.cpu().numpy())
        y_test_full.append(y.cpu().numpy())
    test_preds = np.concatenate(test_preds)
    y_test_full = np.concatenate(y_test_full)
    test_acc = np.sum(test_preds == y_test_full) / len(y_test_full)
    print(f'total number of test data: {len(y_test_full)}, correct={np.sum(test_preds == y_test_full)}, test acc={test_acc:.4f}')
    return test_acc

def _plot_training_history(train_metric, val_metric, best_epoch, title, ylabel="Metric", output_path=None):
    plt.figure(figsize=(8, 6))
    plt.plot(train_metric, label='train')
    plt.plot(val_metric, label='val')
    plt.axvline(x=best_epoch, color='r', linestyle='--', alpha=0.8)
    plt.xlabel('Epochs')
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend()
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"图片已保存到: {output_path}")
    else:
        plt.show()
    plt.close()

### 4. mRNA Expression Prediction

def prepare_mrna_expression_data(data_file, value_0=0, value_2=2):
    data_df = pd.read_csv(data_file)
    data_df = data_df[data_df["Value"].isin([value_0, value_2])]
    raw_seqs = []
    labels = []
    for index, row in data_df.iterrows():
        raw_seq = (str(index), row["Sequence"])
        raw_seqs.append(raw_seq)
        labels.append(row["Value"])
    labels = np.array(labels)
    labels = (labels == value_2) * 1  # Binary class: (0: low, 1: high)
    return raw_seqs, labels, data_df

def split_data(token_embeddings, labels, splits):
    train_list = (splits == "train")
    val_list = (splits == "val")
    test_list = (splits == "test")
    x_train, y_train = token_embeddings[train_list], labels[train_list]
    x_val, y_val = token_embeddings[val_list], labels[val_list]
    x_test, y_test = token_embeddings[test_list], labels[test_list]
    return x_train, y_train, x_val, y_val, x_test, y_test

### 5. Utility for Classification Task with Multi-Class RNA Types

def get_class_distribution(labels):
    classes, counts = np.unique(labels, return_counts=True)
    distribution = counts / counts.sum()
    return dict(zip(classes, distribution))

def stratified_split(token_embeddings, labels, test_size=0.2, val_size=0.2, seed=42):
    x_train_val, x_test, y_train_val, y_test = train_test_split(token_embeddings, labels, test_size=test_size, random_state=seed, stratify=labels)
    x_train, x_val, y_train, y_val = train_test_split(x_train_val, y_train_val, test_size=val_size, random_state=seed, stratify=y_train_val)
    return x_train, y_train, x_val, y_val, x_test, y_test
