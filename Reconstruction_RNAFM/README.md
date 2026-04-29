# RNA-FM 模型使用指南

## 如何区分是否需要训练？

### 🔵 **不需要训练的功能**（直接使用预训练模型）

这些功能使用的是已经预训练好的 RNA-FM 模型，可以直接使用，无需训练：

#### 1. **序列嵌入生成** (`embed_sequences`)
- **用途**：将 RNA 序列转换为数值向量（嵌入）
- **模型**：使用预训练的 RNA-FM 或 mRNA-FM 模型
- **是否需要训练**：❌ **不需要**
- **使用场景**：
  - 序列相似性分析
  - 聚类分析
  - 作为下游任务的输入特征

#### 2. **二级结构预测** (`predict_secondary_structure`)
- **用途**：预测 RNA 序列的二级结构
- **模型**：使用预训练的二级结构预测模型（`model_type="ss"`）
- **是否需要训练**：❌ **不需要**
- **使用场景**：
  - 直接预测 RNA 二级结构
  - 分析 RNA 折叠模式
- **输出**：
  - 智能输出：使用 `--output` 参数，自动识别格式
    - 目录路径：自动生成所有格式（.png 图片和 .ct 结构文件），使用序列ID命名
    - 文件路径：根据扩展名自动识别（.npy, .png, .ct 等）

#### 3. **t-SNE 可视化**
- **用途**：将高维嵌入降维到 2D 进行可视化
- **是否需要训练**：❌ **不需要**（这是数据分析方法，不是模型）

---

### 🟡 **需要训练的功能**（在预训练嵌入基础上训练分类器）

这些功能需要在预训练模型生成的嵌入基础上，训练一个简单的分类器：

#### 1. **RNA 家族分类** (`RNATypeClassifier`)
- **用途**：将 RNA 序列分类到不同的 RNA 家族
- **训练流程**：
  1. 使用预训练模型生成嵌入（不需要训练）
  2. 在嵌入基础上训练一个线性分类器（需要训练）
- **是否需要训练**：✅ **需要训练分类器**
- **训练步骤**：
  ```python
  # 1. 生成嵌入（不需要训练）
  embedder = RNAFMEmbedder(model_type="rna")
  embeddings = embedder.embed_sequences(sequences, mean_pool=True)
  
  # 2. 准备数据
  x_train, y_train, x_val, y_val, x_test, y_test = stratified_split(...)
  
  # 3. 创建分类器模型
  model = RNATypeClassifier(in_dim, num_class)
  
  # 4. 训练分类器（需要训练）
  train_classifier(model, train_loader, val_loader, test_loader, ...)
  ```

#### 2. **mRNA 表达水平预测**
- **用途**：预测 mRNA 的表达水平（高/低）
- **训练流程**：
  1. 使用预训练模型生成嵌入（不需要训练）
  2. 在嵌入基础上训练一个二分类器（需要训练）
- **是否需要训练**：✅ **需要训练分类器**
- **训练步骤**：与 RNA 家族分类类似

---

## 快速判断方法

### 判断标准：

1. **如果只是调用 `RNAFMEmbedder` 的方法**：
   - `embed_sequences()` → ❌ 不需要训练
   - `predict_secondary_structure()` → ❌ 不需要训练

2. **如果需要创建和训练 `RNATypeClassifier`**：
   - ✅ 需要训练分类器

3. **如果只是数据分析和可视化**：
   - t-SNE、绘图等 → ❌ 不需要训练

---

## 使用示例

### 示例1：直接使用（不需要训练）

```python
from function import RNAFMEmbedder

# 初始化模型（自动加载预训练权重）
embedder = RNAFMEmbedder(model_type="ss")

# 生成嵌入（不需要训练）
sequences = [("RNA1", "GGGUGCGAUCAUACCAGCACUAAUGCCCUCCUGGGAAGUCCUCGUGUUGCACCCCU")]
embeddings = embedder.embed_sequences(sequences)

# 预测二级结构（不需要训练）
ss_prob = embedder.predict_secondary_structure(sequences)
```

### 示例2：需要训练分类器

```python
from function import RNAFMEmbedder, RNATypeClassifier, train_classifier, stratified_split

# 1. 生成嵌入（不需要训练）
embedder = RNAFMEmbedder(model_type="rna")
embeddings = embedder.embed_sequences(sequences, mean_pool=True)

# 2. 准备数据
x_train, y_train, x_val, y_val, x_test, y_test = stratified_split(embeddings, labels)

# 3. 创建分类器
model = RNATypeClassifier(in_dim=embeddings.shape[1], num_class=num_classes)

# 4. 训练分类器（需要训练）
train_classifier(model, train_loader, val_loader, test_loader, ...)
```

---

## 运行 main.py

```bash
# 运行示例1：嵌入和二级结构（不需要训练）
python main.py --example 1

# 运行示例2：RNA 家族聚类（不需要训练）
python main.py --example 2

# 运行示例3：RNA 家族分类（需要训练）
python main.py --example 3

# 运行示例4：mRNA 表达预测（需要训练）
python main.py --example 4
```

---

## 图片输出功能

所有可视化功能都支持保存图片到文件：

| 功能 | 图片输出参数 | 保存的文件 |
|------|------------|-----------|
| 二级结构预测 | `--output` (目录) | 自动生成所有格式（.png 和 .ct），使用序列ID命名 |
| 二级结构预测 | `--output` (文件) | 根据扩展名自动识别格式（.npy, .png, .ct） |
| 聚类可视化 | `--output` | t-SNE 聚类图（.png 等） |
| 分类训练 | `--output` | loss_history.png, accuracy_history.png |
| 表达预测训练 | `--output` | loss_history.png, accuracy_history.png |

**使用示例**：
```bash
# 保存二级结构可视化
# 智能输出：指定目录，自动生成所有格式（使用序列ID命名）
ReRNAFM predict_ss --sequences_file seq.fasta --output ./results/
# 会生成：maqe.png 和 maqe.ct（如果序列ID是 maqe）

# 保存聚类结果
ReRNAFM cluster --fasta_folder /path/to/fasta --output cluster.png

# 保存训练历史
ReRNAFM classify --fasta_folder /path/to/fasta --output ./results/
```

## 总结

| 功能 | 是否需要训练 | 说明 |
|------|------------|------|
| 序列嵌入生成 | ❌ 否 | 使用预训练模型 |
| 二级结构预测 | ❌ 否 | 使用预训练模型 |
| t-SNE 可视化 | ❌ 否 | 数据分析方法 |
| RNA 家族分类 | ✅ 是 | 需要训练分类器 |
| mRNA 表达预测 | ✅ 是 | 需要训练分类器 |

**关键点**：
- RNA-FM 基础模型是预训练的，不需要训练
- 分类任务需要在嵌入基础上训练一个简单的分类器
- 训练分类器通常只需要几分钟到几十分钟，取决于数据量
- **所有图片都可以保存到文件**，适合在无图形界面的服务器环境中使用

