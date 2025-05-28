# Workday 简单 API 爬虫

一个专门用于抓取 Workday 招聘网站职位信息的 Python 爬虫工具。

## 脚本说明

### workday_simple_api.py

这是一个简化的 Workday API 职位爬虫，专门设计用于抓取 Workday 招聘平台的职位数据。

#### 主要功能

- **自动 API 发现**: 自动解析 Workday URL 并构建正确的 API 端点
- **分页抓取**: 支持自动分页，获取所有可用职位
- **完整职位 ID 提取**: 改进的职位 ID 提取算法，支持多种 ID 格式
- **错误处理**: 包含重试机制和详细的错误日志
- **数据清洗**: 自动清理和标准化职位数据
- **CSV 导出**: 将抓取的数据保存为结构化的 CSV 文件

#### 技术特点

1. **智能 URL 解析**: 
   - 自动从 Workday URL 提取公司信息和站点 ID
   - 构建标准的 API 端点格式: `/wday/cxs/{company}/{site_id}/jobs`

2. **多层职位 ID 提取**:
   - 优先从 `bulletFields` 数组提取职位 ID
   - 备用方案从 `externalPath` 解析 ID
   - 支持多种 ID 字段格式

3. **可靠的分页机制**:
   - 使用 offset/limit 参数进行分页
   - 自动检测最后一页
   - 支持自定义每页数量

4. **完整的数据字段**:
   - job_id: 职位编号
   - title: 职位标题
   - location: 工作地点
   - posting_date: 发布日期
   - url: 职位详情链接
   - company: 公司名称
   - scraped_at: 抓取时间戳

#### 使用方法

```bash
# 基本用法 - 抓取 PulteGroup 职位
python workday_simple_api.py

# 指定其他 Workday 网站
python workday_simple_api.py --url https://company.wd1.myworkdayjobs.com/careers

# 自定义输出文件名
python workday_simple_api.py --output my_jobs.csv

# 调整请求延迟
python workday_simple_api.py --delay 5.0

# 设置最大重试次数
python workday_simple_api.py --max-retries 5
```

### simple_analysis.py

这是一个轻量级的数据分析脚本，用于分析爬虫抓取的职位数据，无需安装 pandas 等重型依赖。

#### 主要功能

- **自动文件检测**: 自动找到 output 目录中最新的 CSV 文件进行分析
- **基础统计**: 提供职位总数、公司信息、数据完整性等基础统计
- **地点分析**: 统计各工作地点的职位数量，显示热门城市排行
- **职位分类**: 基于关键词自动分类职位类型（销售、管理、工程等）
- **数据质量检查**: 检查各字段的数据完整性和覆盖率
- **发布日期分析**: 统计职位发布时间分布

#### 分析内容

1. **数据概览**:
   - 总职位数量
   - 抓取时间
   - 涉及公司

2. **地理分布**:
   - 独特工作地点数量
   - 前10个热门城市及职位数

3. **职位信息**:
   - 示例职位标题
   - 职位URL覆盖率
   - 发布日期分布

4. **数据完整性**:
   - 各字段的数据覆盖率
   - 缺失数据统计

5. **职位分类**:
   - 基于关键词的自动分类
   - 各类别职位数量统计

#### 使用方法

```bash
# 分析最新的抓取数据
python simple_analysis.py
```

#### 输出示例

```
📄 Analyzing: output/pultegroup_jobs_simple_20250524_140443.csv

📊 Job Data Analysis
==================================================
📈 Total jobs scraped: 217
📅 Data scraped on: 2025-05-24
🏢 Companies: Pultegroup
📍 Unique locations: 51

🔝 Top 10 locations:
   Atlanta, GA: 13 jobs
   Charlotte, NC: 12 jobs
   Florence, SC: 11 jobs
   Houston, TX: 10 jobs
   Alpharetta, GA: 9 jobs
   Coppell, TX: 8 jobs
   Brentwood, TN: 7 jobs
   Carmel, IN: 6 jobs
   Myrtle Beach, SC: 6 jobs
   West Palm Beach, FL: 6 jobs

💼 Sample job titles:
   1. Land Project Manager - Savannah, GA
   2. Mortgage Financing Advisor - (Pulte Mortgage)
   3. Sales Administrator - Bluffton, SC
   4. General Sales Manager - Hilton Head, SC
   5. Sales Consultant - Bluffton/Hilton Head, SC

🔗 Jobs with URLs: 217/217 (100.0%)
📅 Jobs with posting dates: 217/217 (100.0%)

📆 Posting date distribution:
   Posted Today: 9 jobs
   Posted Yesterday: 4 jobs
   Posted 2 Days Ago: 2 jobs
   Posted 3 Days Ago: 4 jobs
   Posted 4 Days Ago: 6 jobs

📋 Data completeness:
   job_id: 217/217 (100.0%)
   title: 217/217 (100.0%)
   location: 217/217 (100.0%)
   posting_date: 217/217 (100.0%)
   url: 217/217 (100.0%)
   company: 217/217 (100.0%)
   scraped_at: 217/217 (100.0%)

🏷️ Job categories (based on titles):
   Sales: 65 jobs
   Management: 58 jobs
   Construction: 32 jobs
   Finance: 28 jobs
   Administrative: 15 jobs
   Marketing: 8 jobs
   Engineering: 3 jobs

✅ Analysis complete!
📁 Full data available in: output/pultegroup_jobs_simple_20250524_140443.csv
```

## 输出结果

### CSV 文件格式

脚本会在 `output/` 目录下生成 CSV 文件，文件名格式为：`{company}_jobs_simple_{timestamp}.csv`

#### 数据字段说明

| 字段名 | 描述 | 示例 |
|--------|------|------|
| job_id | 职位编号 | JR4032 |
| title | 职位标题 | Land Project Manager - Savannah, GA |
| location | 工作地点 | Hilton Head, SC |
| posting_date | 发布日期 | Posted Today |
| url | 职位详情链接 | https://pultegroup.wd1.myworkdayjobs.com/job/... |
| company | 公司名称 | Pultegroup |
| scraped_at | 抓取时间 | 2025-05-24T14:04:21.268614 |

### 实际抓取结果示例

以 PulteGroup 为例的抓取结果：

#### 统计信息
- **总职位数**: 217 个
- **职位 ID 完整性**: 217/217 (100%)
- **覆盖地点**: 51 个城市
- **数据完整性**: 100%

#### 热门工作地点
1. Atlanta, GA - 13 个职位
2. Charlotte, NC - 12 个职位  
3. Florence, SC - 11 个职位
4. Houston, TX - 10 个职位
5. Alpharetta, GA - 9 个职位

#### 职位类型分布
- 销售类 (Sales): 约 30%
- 建筑管理 (Construction): 约 25%
- 土地开发 (Land Development): 约 15%
- 客户服务 (Customer Care): 约 10%
- 金融财务 (Finance): 约 8%
- 其他专业职位: 约 12%

#### 示例数据记录

```csv
job_id,title,location,posting_date,url,company,scraped_at
JR4032,"Land Project Manager - Savannah, GA","Hilton Head, SC",Posted Today,https://pultegroup.wd1.myworkdayjobs.com/job/Hilton-Head-SC/Land-Project-Manager---Hilton-Head--SC_JR4032,Pultegroup,2025-05-24T14:04:21.268614
JR7353,Mortgage Financing Advisor - (Pulte Mortgage),"Hilton Head, SC",Posted Today,https://pultegroup.wd1.myworkdayjobs.com/job/Hilton-Head-SC/Mortgage-Financing-Advisor----Pulte-Mortgage-_JR7353,Pultegroup,2025-05-24T14:04:21.268614
JR7452,"Sales Administrator - Bluffton, SC","Hilton Head, SC",Posted Today,https://pultegroup.wd1.myworkdayjobs.com/job/Hilton-Head-SC/Sales-Administrator---Bluffton--SC_JR7452,Pultegroup,2025-05-24T14:04:21.268614
```

### 运行日志示例

```
🚀 Starting Simple Workday API job scraping...
📍 Target URL: https://pultegroup.wd1.myworkdayjobs.com/PGI
🏢 Company: pultegroup
🆔 Site ID: PGI
--------------------------------------------------
🚀 Starting simple Workday API scraping...
🎯 API URL: https://pultegroup.wd1.myworkdayjobs.com/wday/cxs/pultegroup/PGI/jobs

📄 Fetching page with offset 0...
  📡 API request (attempt 1): offset=0
📦 Found 20 jobs in response
✅ Found 20 jobs (total: 20)

📄 Fetching page with offset 20...
  📡 API request (attempt 1): offset=20
📦 Found 20 jobs in response
✅ Found 20 jobs (total: 40)

...

📄 Fetching page with offset 200...
  📡 API request (attempt 1): offset=200
📦 Found 17 jobs in response
✅ Found 17 jobs (total: 217)
📄 Received fewer jobs than limit, assuming last page

✅ Successfully scraped 217 jobs!
💾 Saved 217 jobs to output/pultegroup_jobs_simple_20250524_140443.csv
📄 Data saved to: output/pultegroup_jobs_simple_20250524_140443.csv

📊 Summary:
   Total jobs: 217
   Jobs with job_id: 217/217 (100.0%)
   Sample jobs with IDs:
     1. [JR4032] Land Project Manager - Savannah, GA
     2. [JR7353] Mortgage Financing Advisor - (Pulte Mortgage)
     3. [JR7452] Sales Administrator - Bluffton, SC
```

## 依赖要求

```
requests>=2.31.0
```

## 注意事项

1. **请求频率**: 默认每次请求间隔 2 秒，避免对服务器造成过大压力
2. **数据准确性**: 所有数据直接来源于 Workday API，保证数据的实时性和准确性
3. **兼容性**: 适用于所有使用标准 Workday 平台的公司招聘网站
4. **错误处理**: 包含完整的错误处理和重试机制，确保抓取的稳定性

## 🤝 Contributing

Feel free to submit issues, feature requests, or pull requests to improve the scraper.

## 📝 License

This project is provided as-is for educational and research purposes.

## 🔄 Updates

- **v2.0**: Enhanced scraper with multiple strategies and better error handling
- **v1.0**: Basic scraper with Selenium support

---

**Happy scraping! 🎉**

For questions or issues, please check the troubleshooting section or create an issue in the repository. 