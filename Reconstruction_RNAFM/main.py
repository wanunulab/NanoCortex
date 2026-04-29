#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RNA-FM 模型使用示例
展示如何使用 function.py 中的各种功能

重要说明：哪些功能需要训练，哪些不需要？
===========================================

【不需要训练的功能】（直接使用预训练模型）：
1. 序列嵌入生成 (embed_sequences) - 使用预训练的 RNA-FM 模型
2. 二级结构预测 (predict_secondary_structure) - 使用预训练的二级结构模型
3. t-SNE 可视化 - 纯数据分析，不需要训练

【需要训练的功能】（在预训练嵌入基础上训练分类器）：
1. RNA 家族分类 - 需要训练 RNATypeClassifier
2. mRNA 表达水平预测 - 需要训练分类器（类似 RNA 家族分类）

训练流程：
1. 使用预训练模型生成嵌入
2. 在嵌入基础上训练一个简单的分类器（线性层）
3. 保存训练好的分类器用于后续预测
"""

import os
import sys
import argparse
import numpy as np
import torch
from torch.utils.data import DataLoader

from function import (
    RNAFMEmbedder,
    load_fasta_folder_as_tuples,
    perform_tsne,
    plot_tsne_embeddings,
    plot_secondary_structure,
    matrix2ct,
    RNATypeDataset,
    RNATypeClassifier,
    train_classifier,
    prepare_mrna_expression_data,
    stratified_split,
    get_class_distribution
)


def example_1_embedding_and_secondary_structure(
    sequences=None,
    model_type="ss",
    device=None,
    repr_layer=12,
    mean_pool=True,
    batch_size=16
):
    """
    示例1：生成嵌入和预测二级结构（不需要训练）
    
    参数:
        sequences: 序列列表，格式为 [("seq_id", "sequence"), ...]
                   如果为 None，则使用默认示例序列
        model_type: 模型类型 ("ss", "rna", "mrna")
        device: 设备 ("cpu", "cuda")，如果为 None 则自动选择
        repr_layer: 表示层编号
        mean_pool: 是否对序列长度维度做平均池化
        batch_size: 批处理大小
    """
    print("=" * 60)
    print("示例1：生成嵌入和预测二级结构（不需要训练）")
    print("=" * 60)
    
    # 如果没有提供序列，使用默认示例
    if sequences is None:
        sequences = [
            ("RNA1", "GGGUGCGAUCAUACCAGCACUAAUGCCCUCCUGGGAAGUCCUCGUGUUGCACCCCU"),
            ("RNA2", "AUGCAUGCAUGCAUGCAUGCAUGCAUGCAUGCAUGCAUGCAUGCAUGCAUGCAUGC"),
        ]
        print("使用默认示例序列")
    
    # 初始化嵌入器（使用预训练模型，不需要训练）
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    embedder = RNAFMEmbedder(model_type=model_type, device=device)
    
    # 1. 生成嵌入（不需要训练）
    print("\n1. 生成序列嵌入...")
    embeddings = embedder.embed_sequences(
        sequences, 
        repr_layer=repr_layer, 
        mean_pool=mean_pool,
        batch_size=batch_size
    )
    print(f"嵌入形状: {embeddings.shape}")
    
    # 2. 预测二级结构（不需要训练）
    print("\n2. 预测二级结构...")
    ss_prob_map = embedder.predict_secondary_structure(sequences)
    print(f"二级结构概率图形状: {ss_prob_map.shape}")
    print(f"二级结构概率图:\n{ss_prob_map[0]}")
    
    return embeddings, ss_prob_map


def example_2_rna_family_clustering(
    fasta_folder,
    model_type="rna",
    device=None,
    repr_layer=12,
    mean_pool=True,
    batch_size=16,
    n_components=2,
    random_state=42,
    output_path=None
):
    """
    示例2：RNA 家族聚类可视化（不需要训练）
    
    参数:
        fasta_folder: 包含 RF*.fasta 文件的文件夹路径
        model_type: 模型类型 ("ss", "rna", "mrna")
        device: 设备 ("cpu", "cuda")，如果为 None 则自动选择
        repr_layer: 表示层编号
        mean_pool: 是否对序列长度维度做平均池化
        batch_size: 批处理大小
        n_components: t-SNE 降维后的维度
        random_state: 随机种子
        output_path: 输出图片路径，如果为 None 则直接显示
    """
    print("\n" + "=" * 60)
    print("示例2：RNA 家族聚类可视化（不需要训练）")
    print("=" * 60)
    
    if not os.path.exists(fasta_folder):
        raise ValueError(f"文件夹 {fasta_folder} 不存在")
    
    # 1. 加载 FASTA 文件
    print("\n1. 加载 FASTA 文件...")
    seqs, labels, rfam_list = load_fasta_folder_as_tuples(fasta_folder)
    print(f"加载了 {len(seqs)} 个序列，来自 {len(rfam_list)} 个 RNA 家族")
    
    # 2. 生成嵌入（不需要训练）
    print("\n2. 生成嵌入...")
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    embedder = RNAFMEmbedder(model_type=model_type, device=device)
    embeddings = embedder.embed_sequences(
        seqs, 
        repr_layer=repr_layer, 
        mean_pool=mean_pool,
        batch_size=batch_size
    )
    print(f"嵌入形状: {embeddings.shape}")
    
    # 3. t-SNE 降维（不需要训练）
    print("\n3. 执行 t-SNE 降维...")
    embeddings_2d = perform_tsne(embeddings, n_components=n_components, random_state=random_state)
    
    # 4. 可视化
    print("\n4. 可视化聚类结果...")
    plot_tsne_embeddings(embeddings_2d, labels, output_path=output_path)
    
    return embeddings_2d, labels, rfam_list


def example_3_rna_family_classification(
    fasta_folder,
    checkpoint_path="rna_family_classifier.pt",
    model_type="rna",
    device=None,
    repr_layer=12,
    mean_pool=True,
    batch_size=16,
    train_batch_size=32,
    test_size=0.2,
    val_size=0.2,
    seed=42,
    num_epochs=50,
    lr=1e-3,
    display_step=10,
    output_path=None
):
    """
    示例3：RNA 家族分类（需要训练分类器）
    
    参数:
        fasta_folder: 包含 RF*.fasta 文件的文件夹路径
        checkpoint_path: 保存训练好的模型的路径
        model_type: 模型类型 ("ss", "rna", "mrna")
        device: 设备 ("cpu", "cuda")，如果为 None 则自动选择
        repr_layer: 表示层编号
        mean_pool: 是否对序列长度维度做平均池化
        batch_size: 嵌入生成时的批处理大小
        train_batch_size: 训练时的批处理大小
        test_size: 测试集比例
        val_size: 验证集比例（相对于训练+验证集）
        seed: 随机种子
        num_epochs: 训练轮数
        lr: 学习率
        display_step: 每隔多少轮显示一次训练进度
    """
    print("\n" + "=" * 60)
    print("示例3：RNA 家族分类（需要训练分类器）")
    print("=" * 60)
    
    if not os.path.exists(fasta_folder):
        raise ValueError(f"文件夹 {fasta_folder} 不存在")
    
    # 1. 加载数据
    print("\n1. 加载数据...")
    seqs, labels, rfam_list = load_fasta_folder_as_tuples(fasta_folder)
    print(f"加载了 {len(seqs)} 个序列，{len(rfam_list)} 个类别")
    
    # 2. 生成嵌入（使用预训练模型，不需要训练）
    print("\n2. 生成嵌入（使用预训练模型）...")
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    embedder = RNAFMEmbedder(model_type=model_type, device=device)
    embeddings = embedder.embed_sequences(
        seqs, 
        repr_layer=repr_layer, 
        mean_pool=mean_pool,
        batch_size=batch_size
    )
    print(f"嵌入形状: {embeddings.shape}")
    
    # 3. 将标签转换为数字
    label_to_idx = {label: idx for idx, label in enumerate(rfam_list)}
    numeric_labels = np.array([label_to_idx[label] for label in labels])
    
    # 4. 划分数据集
    print("\n3. 划分数据集...")
    x_train, y_train, x_val, y_val, x_test, y_test = stratified_split(
        embeddings, numeric_labels, test_size=test_size, val_size=val_size, seed=seed
    )
    print(f"训练集: {len(x_train)}, 验证集: {len(x_val)}, 测试集: {len(x_test)}")
    
    # 5. 创建数据加载器
    train_dataset = RNATypeDataset(x_train, y_train, mean_pool=False)
    val_dataset = RNATypeDataset(x_val, y_val, mean_pool=False)
    test_dataset = RNATypeDataset(x_test, y_test, mean_pool=False)
    
    train_loader = DataLoader(train_dataset, batch_size=train_batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=train_batch_size, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=train_batch_size, shuffle=False)
    
    # 6. 创建分类器模型（需要训练）
    print("\n4. 创建分类器模型...")
    in_dim = embeddings.shape[1]
    num_class = len(rfam_list)
    model = RNATypeClassifier(in_dim, num_class).to(device)
    print(f"模型输入维度: {in_dim}, 类别数: {num_class}")
    
    # 7. 训练分类器（这是需要训练的部分）
    print("\n5. 训练分类器（需要训练）...")
    # 如果指定了输出路径，创建目录
    if output_path:
        os.makedirs(output_path, exist_ok=True)
    test_acc = train_classifier(
        model, train_loader, val_loader, test_loader,
        device=device,
        num_epochs=num_epochs,
        lr=lr,
        checkpoint_path=checkpoint_path,
        display_step=display_step,
        output_path=output_path
    )
    print(f"\n最终测试准确率: {test_acc:.4f}")
    print(f"训练好的模型已保存到: {checkpoint_path}")
    
    # 8. 使用训练好的模型进行预测（示例）
    print("\n6. 使用训练好的模型进行预测...")
    model.load_state_dict(torch.load(checkpoint_path)['model_state_dict'])
    model.eval()
    
    # 预测单个样本
    sample_idx = 0
    sample_emb = torch.tensor(x_test[sample_idx], dtype=torch.float32).unsqueeze(0).to(device)
    with torch.no_grad():
        output = model(sample_emb)
        pred_class = torch.argmax(output, dim=1).item()
    
    print(f"样本 {sample_idx} 的真实类别: {y_test[sample_idx]} ({rfam_list[y_test[sample_idx]]})")
    print(f"样本 {sample_idx} 的预测类别: {pred_class} ({rfam_list[pred_class]})")
    
    return test_acc, model, checkpoint_path


def example_4_mrna_expression_prediction(
    data_file,
    checkpoint_path="mrna_expression_classifier.pt",
    model_type="mrna",
    device=None,
    repr_layer=12,
    mean_pool=True,
    batch_size=16,
    train_batch_size=32,
    value_0=0,
    value_2=2,
    test_size=0.2,
    val_size=0.2,
    seed=42,
    num_epochs=50,
    lr=1e-3,
    display_step=10,
    output_path=None
):
    """
    示例4：mRNA 表达水平预测（需要训练分类器）
    
    参数:
        data_file: 包含表达数据的 CSV 文件路径
        checkpoint_path: 保存训练好的模型的路径
        model_type: 模型类型 ("ss", "rna", "mrna")
        device: 设备 ("cpu", "cuda")，如果为 None 则自动选择
        repr_layer: 表示层编号
        mean_pool: 是否对序列长度维度做平均池化
        batch_size: 嵌入生成时的批处理大小
        train_batch_size: 训练时的批处理大小
        value_0: 低表达值
        value_2: 高表达值
        test_size: 测试集比例
        val_size: 验证集比例（相对于训练+验证集）
        seed: 随机种子
        num_epochs: 训练轮数
        lr: 学习率
        display_step: 每隔多少轮显示一次训练进度
    """
    print("\n" + "=" * 60)
    print("示例4：mRNA 表达水平预测（需要训练分类器）")
    print("=" * 60)
    
    if not os.path.exists(data_file):
        raise ValueError(f"文件 {data_file} 不存在")
    
    # 1. 准备数据
    print("\n1. 准备数据...")
    raw_seqs, labels, data_df = prepare_mrna_expression_data(data_file, value_0=value_0, value_2=value_2)
    print(f"加载了 {len(raw_seqs)} 个序列")
    print(f"类别分布: {get_class_distribution(labels)}")
    
    # 2. 生成嵌入（使用预训练模型，不需要训练）
    print("\n2. 生成嵌入（使用预训练模型）...")
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    embedder = RNAFMEmbedder(model_type=model_type, device=device)
    embeddings = embedder.embed_sequences(
        raw_seqs, 
        repr_layer=repr_layer, 
        mean_pool=mean_pool,
        batch_size=batch_size
    )
    print(f"嵌入形状: {embeddings.shape}")
    
    # 3. 划分数据集（假设数据中有 splits 列）
    # 如果没有 splits 列，使用 stratified_split
    if "splits" in data_df.columns:
        from function import split_data
        splits = data_df["splits"].values
        x_train, y_train, x_val, y_val, x_test, y_test = split_data(embeddings, labels, splits)
    else:
        x_train, y_train, x_val, y_val, x_test, y_test = stratified_split(
            embeddings, labels, test_size=test_size, val_size=val_size, seed=seed
        )
    
    print(f"训练集: {len(x_train)}, 验证集: {len(x_val)}, 测试集: {len(x_test)}")
    
    # 4. 创建数据加载器
    train_dataset = RNATypeDataset(x_train, y_train, mean_pool=False)
    val_dataset = RNATypeDataset(x_val, y_val, mean_pool=False)
    test_dataset = RNATypeDataset(x_test, y_test, mean_pool=False)
    
    train_loader = DataLoader(train_dataset, batch_size=train_batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=train_batch_size, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=train_batch_size, shuffle=False)
    
    # 5. 创建分类器模型（需要训练）
    print("\n3. 创建分类器模型...")
    in_dim = embeddings.shape[1]
    num_class = 2  # 二分类：低表达(0) vs 高表达(1)
    model = RNATypeClassifier(in_dim, num_class).to(device)
    
    # 6. 训练分类器（这是需要训练的部分）
    print("\n4. 训练分类器（需要训练）...")
    # 如果指定了输出路径，创建目录
    if output_path:
        os.makedirs(output_path, exist_ok=True)
    test_acc = train_classifier(
        model, train_loader, val_loader, test_loader,
        device=device,
        num_epochs=num_epochs,
        lr=lr,
        checkpoint_path=checkpoint_path,
        display_step=display_step,
        output_path=output_path
    )
    print(f"\n最终测试准确率: {test_acc:.4f}")
    print(f"训练好的模型已保存到: {checkpoint_path}")
    
    return test_acc, model, checkpoint_path


def sanitize_filename(filename):
    """清理文件名，移除或替换不安全的字符"""
    import re
    # 替换路径分隔符和其他不安全字符
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # 移除多个连续的下划线
    filename = re.sub(r'_+', '_', filename)
    # 移除开头和结尾的下划线
    filename = filename.strip('_')
    return filename


def smart_output_path(output_arg, seq_id, default_ext='.png'):
    """
    智能处理输出路径
    
    参数:
        output_arg: 用户提供的输出路径参数
        seq_id: 序列ID（用于自动命名）
        default_ext: 默认扩展名（当路径是目录时使用）
    
    返回:
        output_dir: 输出目录（如果是目录）或 None
        output_file: 输出文件路径（如果是文件）或 None
        output_type: 输出类型 ('dir', 'npy', 'image', 'ct', 'auto')
    """
    if not output_arg:
        return None, None, None
    
    # 清理序列ID
    safe_seq_id = sanitize_filename(seq_id)
    
    # 检查是否是目录（以 / 结尾或存在且是目录）
    if output_arg.endswith('/') or (os.path.exists(output_arg) and os.path.isdir(output_arg)):
        output_dir = output_arg.rstrip('/')
        os.makedirs(output_dir, exist_ok=True)
        return output_dir, None, 'dir'
    
    # 检查是否有扩展名
    name, ext = os.path.splitext(output_arg)
    
    if not ext:
        # 没有扩展名，当作目录处理
        output_dir = output_arg
        os.makedirs(output_dir, exist_ok=True)
        return output_dir, None, 'dir'
    else:
        # 有扩展名，根据扩展名判断类型
        ext_lower = ext.lower()
        if ext_lower == '.npy':
            return None, output_arg, 'npy'
        elif ext_lower in ['.png', '.jpg', '.jpeg', '.pdf', '.svg']:
            return None, output_arg, 'image'
        elif ext_lower == '.ct':
            return None, output_arg, 'ct'
        else:
            # 未知扩展名，当作目录处理
            output_dir = output_arg
            os.makedirs(output_dir, exist_ok=True)
            return output_dir, None, 'dir'


def load_sequences_from_file(file_path):
    """从文件加载序列"""
    sequences = []
    if file_path.endswith('.fasta') or file_path.endswith('.fa'):
        from Bio import SeqIO
        for record in SeqIO.parse(file_path, 'fasta'):
            sequences.append((record.id, str(record.seq)))
    elif file_path.endswith('.txt'):
        with open(file_path, 'r') as f:
            for idx, line in enumerate(f):
                line = line.strip()
                if line and not line.startswith('#'):
                    sequences.append((f"seq_{idx}", line))
    return sequences


def main():
    """
    主函数：使用子命令结构
    """
    parser = argparse.ArgumentParser(
        prog="ReRNAFM",
        description="RNA-FM 模型工具集 - 用于 RNA 序列分析",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  ReRNAFM embed --sequences "GGGUGCGAUCAUACCAGCACUAAUGCCCUCCUGGGAAGUCCUCGUGUUGCACCCCU"
  ReRNAFM predict_ss --sequences_file sequences.fasta
  ReRNAFM cluster --fasta_folder /path/to/fasta --output result.png
  ReRNAFM classify --fasta_folder /path/to/fasta --checkpoint_path model.pt
  ReRNAFM predict_expression --data_file data.csv --checkpoint_path model.pt
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # ========== 命令1: embed - 生成嵌入 ==========
    parser_embed = subparsers.add_parser(
        'embed', 
        help='生成 RNA 序列嵌入向量',
        description='将 RNA 序列转换为数值向量（嵌入），用于后续分析任务。使用预训练模型，无需训练。',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser_embed.add_argument(
        '--sequences', 
        type=str, 
        nargs='+', 
        help='''RNA 序列列表，直接在命令行提供多个序列。
        示例: --sequences "GGGUGCGAUCAUACCAGCACUAAUGCCCUCCUGGGAAGUCCUCGUGUUGCACCCCU" "AUGCAUGCAUGCAUGCAUGCAUGCAUGCAUGCAUGCAUGCAUGCAUGCAUGCAUGC"
        注意: 必须提供 --sequences 或 --sequences_file 之一'''
    )
    parser_embed.add_argument(
        '--sequences_file', 
        type=str, 
        help='''序列文件路径，支持以下格式:
        - FASTA 格式 (.fasta, .fa): 标准 FASTA 文件，每个序列有 ID 和序列
        - 文本格式 (.txt): 每行一个序列，以 # 开头的行会被忽略
        示例: --sequences_file sequences.fasta
        注意: 必须提供 --sequences 或 --sequences_file 之一'''
    )
    parser_embed.add_argument(
        '--model_type', 
        type=str, 
        default='rna', 
        choices=['ss', 'rna', 'mrna'], 
        help='''模型类型选择:
        - ss: 二级结构预测模型（ResNet）
        - rna: RNA-FM 预训练模型（通用 RNA 序列）
        - mrna: mRNA-FM 预训练模型（专门用于 mRNA）
        默认值: rna
        建议: 对于一般 RNA 序列使用 rna，对于 mRNA 使用 mrna'''
    )
    parser_embed.add_argument(
        '--device', 
        type=str, 
        default=None, 
        choices=['cpu', 'cuda'],
        help='''计算设备选择:
        - cpu: 使用 CPU 计算（较慢但兼容性好）
        - cuda: 使用 GPU 计算（需要 CUDA 支持，速度快）
        默认值: 自动检测，如果有 GPU 则使用 cuda，否则使用 cpu'''
    )
    parser_embed.add_argument(
        '--repr_layer', 
        type=int, 
        default=12, 
        help='''提取表示层的编号。RNA-FM 模型有多个 Transformer 层，不同层捕获不同级别的特征。
        默认值: 12（最后一层，包含最丰富的语义信息）
        范围: 通常为 1-12，数值越大表示越深层的特征'''
    )
    parser_embed.add_argument(
        '--mean_pool', 
        action='store_true', 
        help='''是否对序列长度维度做平均池化。
        如果启用: 输出形状为 (N, d)，每个序列得到一个固定长度的向量
        如果禁用: 输出形状为 (N, L, d)，保留序列长度信息
        默认: 禁用（保留完整序列信息）
        建议: 如果后续需要序列级别的特征（如分类），启用此选项'''
    )
    parser_embed.add_argument(
        '--batch_size', 
        type=int, 
        default=16, 
        help='''批处理大小，即每次处理多少个序列。
        默认值: 16
        建议: 
        - GPU 内存充足时，可以增大（如 32, 64）以提高速度
        - GPU 内存不足时，减小（如 8, 4）以避免内存溢出
        - CPU 模式下，建议使用较小值（如 8）'''
    )
    parser_embed.add_argument(
        '--output', 
        type=str, 
        help='''输出嵌入文件路径，保存为 NumPy 数组格式 (.npy)。
        如果指定，嵌入结果将保存到该文件，可以使用 np.load() 加载。
        示例: --output embeddings.npy
        如果不指定，结果只会在控制台显示形状信息'''
    )
    
    # ========== 命令2: predict_ss - 预测二级结构 ==========
    parser_ss = subparsers.add_parser(
        'predict_ss', 
        help='预测 RNA 二级结构',
        description='预测 RNA 序列的二级结构概率图。使用预训练的二级结构预测模型，无需训练。',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser_ss.add_argument(
        '--sequences', 
        type=str, 
        nargs='+', 
        help='''RNA 序列列表，直接在命令行提供多个序列。
        示例: --sequences "GGGUGCGAUCAUACCAGCACUAAUGCCCUCCUGGGAAGUCCUCGUGUUGCACCCCU"
        注意: 必须提供 --sequences 或 --sequences_file 之一'''
    )
    parser_ss.add_argument(
        '--sequences_file', 
        type=str, 
        help='''序列文件路径，支持以下格式:
        - FASTA 格式 (.fasta, .fa): 标准 FASTA 文件
        - 文本格式 (.txt): 每行一个序列
        示例: --sequences_file sequences.fasta
        注意: 必须提供 --sequences 或 --sequences_file 之一'''
    )
    parser_ss.add_argument(
        '--device', 
        type=str, 
        default=None, 
        choices=['cpu', 'cuda'],
        help='''计算设备选择:
        - cpu: 使用 CPU 计算
        - cuda: 使用 GPU 计算（需要 CUDA 支持）
        默认值: 自动检测，优先使用 GPU'''
    )
    parser_ss.add_argument(
        '--output', 
        type=str, 
        help='''输出路径（智能识别），自动保存所有格式的文件。
        如果指定目录路径（以 / 结尾或不存在且无扩展名）: 
        - 自动创建目录
        - 为每个序列生成所有格式的文件（.png 图片和 .ct 结构文件）
        - 文件名使用序列ID（如 FASTA 中的 >maqe 会生成 maqe.png 和 maqe.ct）
        如果指定文件路径（有扩展名）:
        - .npy: 保存概率图数值结果
        - .png/.jpg/.pdf/.svg: 保存可视化图片
        - .ct: 保存结构文件
        示例: 
        - 目录: --output ./results/ 或 --output ./results
        - 图片: --output result.png
        - 结构: --output result.ct
        - 数值: --output result.npy
        如果不指定，结果只会在控制台显示'''
    )
    parser_ss.add_argument(
        '--threshold', 
        type=float, 
        default=0.5,
        help='''配对概率阈值，用于从概率图确定配对关系。
        默认值: 0.5
        范围: 0.0-1.0
        值越大，配对的置信度要求越高，配对数量可能越少'''
    )
    parser_ss.add_argument(
        '--allow_nc', 
        action='store_true',
        help='''允许非标准配对（non-canonical pairs）。
        默认: 不允许（只允许 AU, UA, GC, CG, GU, UG）
        如果启用，允许所有可能的配对'''
    )
    
    # ========== 命令3: cluster - RNA 家族聚类 ==========
    parser_cluster = subparsers.add_parser(
        'cluster', 
        help='RNA 家族聚类可视化',
        description='对 RNA 序列进行聚类分析，使用 t-SNE 降维并可视化不同 RNA 家族的分布。使用预训练模型生成嵌入，无需训练。',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser_cluster.add_argument(
        '--fasta_folder', 
        type=str, 
        required=True,
        help='''包含 RF*.fasta 文件的文件夹路径（必需参数）。
        文件夹中应包含多个 FASTA 文件，文件名格式为 RF*.fasta（如 RF00001.fasta, RF00002.fasta）。
        每个 FASTA 文件代表一个 RNA 家族，包含该家族的多个序列。
        示例: --fasta_folder /path/to/rfam_data/'''
    )
    parser_cluster.add_argument(
        '--model_type', 
        type=str, 
        default='rna', 
        choices=['ss', 'rna', 'mrna'],
        help='''模型类型选择:
        - ss: 二级结构预测模型
        - rna: RNA-FM 预训练模型（推荐用于一般 RNA 序列）
        - mrna: mRNA-FM 预训练模型（专门用于 mRNA）
        默认值: rna'''
    )
    parser_cluster.add_argument(
        '--device', 
        type=str, 
        default=None, 
        choices=['cpu', 'cuda'],
        help='''计算设备选择:
        - cpu: 使用 CPU 计算
        - cuda: 使用 GPU 计算（推荐，速度快）
        默认值: 自动检测'''
    )
    parser_cluster.add_argument(
        '--batch_size', 
        type=int, 
        default=16, 
        help='''批处理大小，即每次处理多少个序列。
        默认值: 16
        建议: 根据 GPU 内存调整，内存充足时可增大以提高速度'''
    )
    parser_cluster.add_argument(
        '--output', 
        type=str, 
        help='''输出图片路径，保存聚类可视化结果。
        支持格式: .png, .jpg, .pdf, .svg 等 matplotlib 支持的格式
        示例: --output clustering_result.png
        如果不指定，图片将直接显示在屏幕上（需要图形界面）'''
    )
    parser_cluster.add_argument(
        '--n_components', 
        type=int, 
        default=2, 
        help='''t-SNE 降维后的维度数。
        默认值: 2（用于 2D 可视化）
        可选值: 2 或 3（3D 可视化需要支持 3D 的图形库）
        注意: 通常使用 2 维即可，3 维可视化较复杂'''
    )
    parser_cluster.add_argument(
        '--random_state', 
        type=int, 
        default=42, 
        help='''随机种子，用于保证 t-SNE 结果的可重复性。
        默认值: 42
        注意: 使用相同的随机种子可以得到相同的降维结果，便于结果复现'''
    )
    
    # ========== 命令4: classify - RNA 家族分类 ==========
    parser_classify = subparsers.add_parser(
        'classify', 
        help='训练 RNA 家族分类器',
        description='训练一个分类器，将 RNA 序列分类到不同的 RNA 家族。需要训练步骤，训练时间取决于数据量和硬件。',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser_classify.add_argument(
        '--fasta_folder', 
        type=str, 
        required=True,
        help='''包含 RF*.fasta 文件的文件夹路径（必需参数）。
        文件夹中应包含多个 FASTA 文件，每个文件代表一个 RNA 家族。
        示例: --fasta_folder /path/to/rfam_data/'''
    )
    parser_classify.add_argument(
        '--checkpoint_path', 
        type=str, 
        default='rna_family_classifier.pt',
        help='''训练好的模型保存路径。
        默认值: rna_family_classifier.pt
        示例: --checkpoint_path my_model.pt
        注意: 训练过程中会自动保存最佳模型（基于验证集准确率）'''
    )
    parser_classify.add_argument(
        '--model_type', 
        type=str, 
        default='rna', 
        choices=['ss', 'rna', 'mrna'],
        help='''用于生成嵌入的预训练模型类型:
        - ss: 二级结构预测模型
        - rna: RNA-FM 预训练模型（推荐）
        - mrna: mRNA-FM 预训练模型
        默认值: rna'''
    )
    parser_classify.add_argument(
        '--device', 
        type=str, 
        default=None, 
        choices=['cpu', 'cuda'],
        help='''计算设备选择:
        - cpu: 使用 CPU 计算（较慢）
        - cuda: 使用 GPU 计算（强烈推荐，训练速度快）
        默认值: 自动检测'''
    )
    parser_classify.add_argument(
        '--batch_size', 
        type=int, 
        default=16, 
        help='''生成嵌入时的批处理大小。
        默认值: 16
        注意: 这是生成嵌入时的批大小，与训练批大小（--train_batch_size）不同
        建议: 根据 GPU 内存调整'''
    )
    parser_classify.add_argument(
        '--train_batch_size', 
        type=int, 
        default=32, 
        help='''训练分类器时的批处理大小。
        默认值: 32
        建议: 
        - 数据量大时，可以增大（如 64, 128）以加快训练
        - GPU 内存不足时，减小（如 16, 8）
        - 通常比嵌入批大小（--batch_size）大一些'''
    )
    parser_classify.add_argument(
        '--test_size', 
        type=float, 
        default=0.2, 
        help='''测试集占总数据的比例（用于最终评估模型性能）。
        默认值: 0.2（即 20%% 的数据作为测试集）
        范围: 0.0-1.0
        注意: 测试集在训练过程中不会使用，只在最后评估时使用'''
    )
    parser_classify.add_argument(
        '--val_size', 
        type=float, 
        default=0.2, 
        help='''验证集占训练+验证数据的比例（用于选择最佳模型）。
        默认值: 0.2（即训练+验证数据中的 20%% 作为验证集）
        范围: 0.0-1.0
        注意: 验证集用于监控训练过程，选择最佳模型，不参与参数更新'''
    )
    parser_classify.add_argument(
        '--seed', 
        type=int, 
        default=42, 
        help='''随机种子，用于保证数据划分和训练过程的可重复性。
        默认值: 42
        注意: 使用相同的随机种子可以得到相同的数据划分和训练结果'''
    )
    parser_classify.add_argument(
        '--num_epochs', 
        type=int, 
        default=50, 
        help='''训练轮数（epochs），即完整遍历训练集的次数。
        默认值: 50
        建议: 
        - 数据量大时，可以适当减少（如 30-50）
        - 数据量小时，可以增加（如 100-200）
        - 观察验证集准确率，如果不再提升可以提前停止'''
    )
    parser_classify.add_argument(
        '--lr', 
        type=float, 
        default=1e-3, 
        help='''学习率，控制模型参数更新的步长。
        默认值: 0.001 (1e-3)
        建议: 
        - 如果损失不下降，可以尝试增大（如 1e-2）
        - 如果损失震荡，可以减小（如 1e-4）
        - 通常范围: 1e-5 到 1e-2'''
    )
    parser_classify.add_argument(
        '--display_step', 
        type=int, 
        default=10, 
        help='''每隔多少轮（epochs）显示一次训练进度。
        默认值: 10（即每 10 轮显示一次训练和验证的损失、准确率）
        设置为 0 则不显示中间进度（只在最后显示测试结果）
        建议: 训练轮数多时可以设置大一些（如 20），轮数少时可以设置小一些（如 5）'''
    )
    parser_classify.add_argument(
        '--output', 
        type=str, 
        default=None,
        help='''输出路径，用于保存训练过程中的图片（损失曲线和准确率曲线）。
        如果指定目录路径（以 / 结尾或存在且是目录），训练历史图片将保存到该目录：
        - loss_history.png: 损失曲线
        - accuracy_history.png: 准确率曲线
        如果指定文件路径，将作为目录路径使用
        如果不指定，图片将直接显示在屏幕上（需要图形界面）
        示例: --output ./training_results/'''
    )
    
    # ========== 命令5: predict_expression - mRNA 表达预测 ==========
    parser_expr = subparsers.add_parser(
        'predict_expression', 
        help='训练 mRNA 表达水平预测模型',
        description='训练一个二分类器，预测 mRNA 的表达水平（高表达/低表达）。需要训练步骤。',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser_expr.add_argument(
        '--data_file', 
        type=str, 
        required=True, 
        help='''表达数据 CSV 文件路径（必需参数）。
        CSV 文件应包含以下列:
        - Sequence: RNA 序列（必需）
        - Value: 表达值（必需，用于二分类）
        - splits: 数据划分（可选，train/val/test）
        示例: --data_file expression_data.csv'''
    )
    parser_expr.add_argument(
        '--checkpoint_path', 
        type=str, 
        default='mrna_expression_classifier.pt',
        help='''训练好的模型保存路径。
        默认值: mrna_expression_classifier.pt
        示例: --checkpoint_path expression_model.pt
        注意: 训练过程中会自动保存最佳模型'''
    )
    parser_expr.add_argument(
        '--model_type', 
        type=str, 
        default='mrna', 
        choices=['ss', 'rna', 'mrna'],
        help='''用于生成嵌入的预训练模型类型:
        - ss: 二级结构预测模型
        - rna: RNA-FM 预训练模型
        - mrna: mRNA-FM 预训练模型（推荐用于 mRNA）
        默认值: mrna'''
    )
    parser_expr.add_argument(
        '--device', 
        type=str, 
        default=None, 
        choices=['cpu', 'cuda'],
        help='''计算设备选择:
        - cpu: 使用 CPU 计算
        - cuda: 使用 GPU 计算（强烈推荐）
        默认值: 自动检测'''
    )
    parser_expr.add_argument(
        '--batch_size', 
        type=int, 
        default=16, 
        help='''生成嵌入时的批处理大小。
        默认值: 16
        注意: 这是生成嵌入时的批大小，与训练批大小不同'''
    )
    parser_expr.add_argument(
        '--train_batch_size', 
        type=int, 
        default=32, 
        help='''训练分类器时的批处理大小。
        默认值: 32
        建议: 根据 GPU 内存和数据量调整'''
    )
    parser_expr.add_argument(
        '--value_0', 
        type=int, 
        default=0, 
        help='''CSV 文件中表示低表达的值。
        默认值: 0
        注意: 只有 Value 列中等于 --value_0 或 --value_2 的数据才会被使用
        示例: 如果数据中低表达标记为 0，则使用默认值'''
    )
    parser_expr.add_argument(
        '--value_2', 
        type=int, 
        default=2, 
        help='''CSV 文件中表示高表达的值。
        默认值: 2
        注意: 只有 Value 列中等于 --value_0 或 --value_2 的数据才会被使用
        示例: 如果数据中高表达标记为 2，则使用默认值
        分类结果: value_0 -> 类别 0（低表达），value_2 -> 类别 1（高表达）'''
    )
    parser_expr.add_argument(
        '--test_size', 
        type=float, 
        default=0.2, 
        help='''测试集占总数据的比例（如果 CSV 中没有 splits 列）。
        默认值: 0.2（即 20%% 的数据作为测试集）
        范围: 0.0-1.0
        注意: 如果 CSV 文件中有 splits 列，则忽略此参数，使用 splits 列进行划分'''
    )
    parser_expr.add_argument(
        '--val_size', 
        type=float, 
        default=0.2, 
        help='''验证集占训练+验证数据的比例（如果 CSV 中没有 splits 列）。
        默认值: 0.2
        范围: 0.0-1.0
        注意: 如果 CSV 文件中有 splits 列，则忽略此参数'''
    )
    parser_expr.add_argument(
        '--seed', 
        type=int, 
        default=42, 
        help='''随机种子，用于保证数据划分和训练过程的可重复性。
        默认值: 42
        注意: 只有在 CSV 中没有 splits 列时才会使用此参数'''
    )
    parser_expr.add_argument(
        '--num_epochs', 
        type=int, 
        default=50, 
        help='''训练轮数（epochs）。
        默认值: 50
        建议: 根据数据量和验证集表现调整，通常 30-100 轮足够'''
    )
    parser_expr.add_argument(
        '--lr', 
        type=float, 
        default=1e-3, 
        help='''学习率，控制模型参数更新的步长。
        默认值: 0.001 (1e-3)
        建议: 根据训练损失变化调整，范围通常在 1e-5 到 1e-2'''
    )
    parser_expr.add_argument(
        '--display_step', 
        type=int, 
        default=10, 
        help='''每隔多少轮显示一次训练进度。
        默认值: 10
        设置为 0 则不显示中间进度
        建议: 根据训练轮数调整，轮数多时设置大一些'''
    )
    parser_expr.add_argument(
        '--output', 
        type=str, 
        default=None,
        help='''输出路径，用于保存训练过程中的图片（损失曲线和准确率曲线）。
        如果指定目录路径（以 / 结尾或存在且是目录），训练历史图片将保存到该目录：
        - loss_history.png: 损失曲线
        - accuracy_history.png: 准确率曲线
        如果指定文件路径，将作为目录路径使用
        如果不指定，图片将直接显示在屏幕上（需要图形界面）
        示例: --output ./training_results/'''
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # ========== 处理 embed 命令 ==========
    if args.command == 'embed':
        # 准备序列
        sequences = []
        if args.sequences:
            for idx, seq in enumerate(args.sequences):
                sequences.append((f"seq_{idx}", seq))
        elif args.sequences_file:
            if not os.path.exists(args.sequences_file):
                parser.error(f"文件不存在: {args.sequences_file}")
            sequences = load_sequences_from_file(args.sequences_file)
        else:
            parser.error("需要提供 --sequences 或 --sequences_file 参数")
        
        # 生成嵌入
        result = example_1_embedding_and_secondary_structure(
            sequences=sequences,
            model_type=args.model_type,
            device=args.device,
            repr_layer=args.repr_layer,
            mean_pool=args.mean_pool,
            batch_size=args.batch_size
        )
        embeddings, _ = result
        
        # 保存嵌入
        if args.output:
            np.save(args.output, embeddings)
            print(f"\n嵌入已保存到: {args.output}")
    
    # ========== 处理 predict_ss 命令 ==========
    elif args.command == 'predict_ss':
        # 准备序列
        sequences = []
        if args.sequences:
            for idx, seq in enumerate(args.sequences):
                sequences.append((f"seq_{idx}", seq))
        elif args.sequences_file:
            if not os.path.exists(args.sequences_file):
                parser.error(f"文件不存在: {args.sequences_file}")
            sequences = load_sequences_from_file(args.sequences_file)
        else:
            parser.error("需要提供 --sequences 或 --sequences_file 参数")
        
        # 预测二级结构
        embedder = RNAFMEmbedder(model_type="ss", device=args.device)
        ss_prob_map = embedder.predict_secondary_structure(sequences)
        
        print(f"二级结构概率图形状: {ss_prob_map.shape}")
        print(f"二级结构概率图:\n{ss_prob_map[0]}")
        
        # 智能处理输出
        if args.output:
            # 使用第一个序列的ID作为默认名称（如果只有一个序列）
            default_seq_id = sequences[0][0] if len(sequences) == 1 else "seq"
            output_dir, output_file, output_type = smart_output_path(args.output, default_seq_id)
            
            if output_type == 'dir':
                # 目录模式：为每个序列生成所有格式的文件
                for idx, (seq_id, seq) in enumerate(sequences):
                    safe_seq_id = sanitize_filename(seq_id)
                    
                    # 获取对应的概率图
                    if len(ss_prob_map.shape) == 3:
                        prob_map = ss_prob_map[idx]
                    else:
                        prob_map = ss_prob_map
                    
                    # 生成图片（使用序列ID命名，如 maqe.png）
                    png_file = os.path.join(output_dir, f"{safe_seq_id}.png")
                    # plot_secondary_structure 需要 (N, L, L) 或 (L, L) 格式
                    if len(prob_map.shape) == 2:
                        # 如果是 2D，需要添加批次维度
                        if hasattr(prob_map, 'unsqueeze'):
                            prob_map_for_plot = prob_map.unsqueeze(0)
                        else:
                            prob_map_for_plot = np.expand_dims(prob_map, 0)
                    else:
                        prob_map_for_plot = prob_map
                    plot_secondary_structure(prob_map_for_plot, sequence_id=seq_id, output_path=png_file)
                    print(f"图片已保存到: {png_file}")
                    
                    # 生成结构文件
                    ct_file = os.path.join(output_dir, f"{safe_seq_id}.ct")
                    matrix2ct(prob_map, seq, safe_seq_id, ct_file, 
                             threshold=args.threshold, allow_nc=args.allow_nc)
                    print(f"结构文件已保存到: {ct_file}")
                    
            elif output_type == 'npy':
                # 保存数值结果
                np.save(output_file, ss_prob_map.cpu().numpy())
                print(f"\n数值结果已保存到: {output_file}")
                
            elif output_type == 'image':
                # 保存图片
                if len(sequences) == 1:
                    plot_secondary_structure(ss_prob_map, sequence_id=sequences[0][0], output_path=output_file)
                    print(f"\n图片已保存到: {output_file}")
                else:
                    # 多个序列时，为每个序列生成单独的图片
                    name, ext = os.path.splitext(output_file)
                    for idx, (seq_id, _) in enumerate(sequences):
                        safe_seq_id = sanitize_filename(seq_id)
                        img_file = f"{name}_{safe_seq_id}{ext}"
                        plot_secondary_structure(ss_prob_map[idx:idx+1], sequence_id=seq_id, output_path=img_file)
                        print(f"图片已保存到: {img_file}")
                        
            elif output_type == 'ct':
                # 保存结构文件
                if len(sequences) == 1:
                    matrix2ct(ss_prob_map[0] if len(ss_prob_map.shape) == 3 else ss_prob_map,
                             sequences[0][1], sanitize_filename(sequences[0][0]), output_file,
                             threshold=args.threshold, allow_nc=args.allow_nc)
                    print(f"\n结构文件已保存到: {output_file}")
                else:
                    # 多个序列时，为每个序列生成单独的文件
                    name, ext = os.path.splitext(output_file)
                    for idx, (seq_id, seq) in enumerate(sequences):
                        safe_seq_id = sanitize_filename(seq_id)
                        ct_file = f"{name}_{safe_seq_id}{ext}"
                        prob_map = ss_prob_map[idx] if len(ss_prob_map.shape) == 3 else ss_prob_map
                        matrix2ct(prob_map, seq, safe_seq_id, ct_file,
                                 threshold=args.threshold, allow_nc=args.allow_nc)
                        print(f"结构文件已保存到: {ct_file}")
        else:
            # 如果没有指定输出，提示用户
            print("\n提示: 使用 --output 参数可以保存结果（支持目录、.npy、.png、.ct 等格式）")
    
    # ========== 处理 cluster 命令 ==========
    elif args.command == 'cluster':
        if not os.path.exists(args.fasta_folder):
            parser.error(f"文件夹不存在: {args.fasta_folder}")
        
        result = example_2_rna_family_clustering(
            fasta_folder=args.fasta_folder,
            model_type=args.model_type,
            device=args.device,
            batch_size=args.batch_size,
            n_components=args.n_components,
            random_state=args.random_state,
            output_path=args.output_path
        )
    
    # ========== 处理 classify 命令 ==========
    elif args.command == 'classify':
        if not os.path.exists(args.fasta_folder):
            parser.error(f"文件夹不存在: {args.fasta_folder}")
        
        result = example_3_rna_family_classification(
            fasta_folder=args.fasta_folder,
            checkpoint_path=args.checkpoint_path,
            model_type=args.model_type,
            device=args.device,
            batch_size=args.batch_size,
            train_batch_size=args.train_batch_size,
            test_size=args.test_size,
            val_size=args.val_size,
            seed=args.seed,
            num_epochs=args.num_epochs,
            lr=args.lr,
            display_step=args.display_step,
            output_path=args.output_path
        )
    
    # ========== 处理 predict_expression 命令 ==========
    elif args.command == 'predict_expression':
        if not os.path.exists(args.data_file):
            parser.error(f"文件不存在: {args.data_file}")
        
        result = example_4_mrna_expression_prediction(
            data_file=args.data_file,
            checkpoint_path=args.checkpoint_path,
            model_type=args.model_type,
            device=args.device,
            batch_size=args.batch_size,
            train_batch_size=args.train_batch_size,
            value_0=args.value_0,
            value_2=args.value_2,
            test_size=args.test_size,
            val_size=args.val_size,
            seed=args.seed,
            num_epochs=args.num_epochs,
            lr=args.lr,
            display_step=args.display_step,
            output_path=args.output_path
        )


if __name__ == "__main__":
    main()

