# AI 广告视频批量生成自动化系统 MVP Plan

## 1. 项目目标

项目目录名：`ai-ad-video-automation/`

第一版 MVP 目标是完成一个可面试展示的 AI 应用闭环：

```text
CSV 导入任务
-> LLM/mock LLM 生成广告文案
-> Pydantic 结构化校验
-> Playwright 提交 mock 剪辑平台
-> 获得 platform_job_id
-> FastAPI 记录状态、日志和失败原因
-> Streamlit 展示与触发流程
```

项目重点是 AI 应用集成、结构化输出、Playwright 自动化、任务状态管理和工程化闭环。不做真实视频剪辑、不训练模型、不接真实第三方平台、不引入复杂队列或微服务。

## 2. MVP 范围

必须做：

- [x] ~~仅支持 CSV 批量导入任务。~~
- [x] ~~每条任务包含视频路径、品牌名、产品类型、核心卖点、目标用户、投放平台、文案风格、模板 ID。~~
- [x] ~~使用 Pydantic 定义并校验广告文案结构。~~
- [x] ~~支持 `LLM_PROVIDER=mock` 演示模式。~~
- [x] ~~支持 KIMI / OpenAI-compatible 真实 API 模式配置入口。~~
- [x] ~~真实 API 模式失败时必须报错并记录失败原因，不静默 fallback 到 mock。~~
- [x] ~~使用 FastAPI 提供任务导入、查询、文案生成、文案重试接口。~~
- [x] ~~使用 SQLite + SQLModel 保存任务和文案结果。~~
- [x] ~~使用 Python Playwright 操作本地 mock 剪辑平台。~~
- [x] ~~使用 FastAPI 提供自动化提交、自动化重试接口。~~
- [x] ~~使用 SQLite + SQLModel 保存自动化运行记录、截图路径、日志路径。~~
- [x] ~~使用 Streamlit Dashboard 调用 FastAPI API 展示和触发任务流程。~~
- [x] ~~pytest 第一版覆盖 `import_service`、copy schema、`task_state`。~~
- [x] ~~pytest Phase 2 覆盖 copy service 成功、失败和真实 provider 不 fallback。~~

暂时不做：

- [x] ~~Excel 导入。第一版明确不支持。~~
- [x] ~~真实视频剪辑、真实视频生成模型。~~
- [x] ~~真实第三方剪辑平台接入。~~
- [x] ~~`SUCCESS` 状态。~~
- [x] ~~`RETRYING` 长期状态。~~
- [x] ~~Celery / Redis / 分布式队列。~~
- [x] ~~多用户、权限系统、复杂模板管理。~~
- [x] ~~Playwright e2e pytest 可作为 Phase 4 optional，不阻塞 MVP。~~

## 3. 推荐架构

- [x] ~~`FastAPI Backend`：任务导入、状态查询、文案生成、文案重试。~~
- [x] ~~`SQLite + SQLModel`：保存任务状态和文案结果。~~
- [x] ~~`LLM Copy Service`：LangChain prompt 流程，Pydantic 结构化输出校验。~~
- [x] ~~`Playwright Automation Service`：模拟人工登录 mock 平台、填写表单、选择模板、提交任务。~~
- [x] ~~`Mock Platform`：本地 FastAPI + HTML 页面，模拟第三方自动剪辑平台。~~
- [x] ~~`Streamlit Dashboard`：只通过 FastAPI API 读写任务，不直接访问数据库。~~
- [x] ~~`pytest`：优先覆盖纯业务逻辑、schema 校验和状态流转。~~

默认服务：

- Backend：`http://localhost:8000`
- Mock platform：`http://localhost:8001`
- Dashboard：Streamlit 本地页面

## 4. 目录结构

```text
ai-ad-video-automation/
  app/
    main.py
    config.py
    db.py
    models.py
    schemas.py
    api/
      tasks.py
      copywriting.py
      automation.py
    services/
      import_service.py
      copy_service.py
      automation_service.py
      task_state.py
    prompts/
      ad_copy_prompt.txt
    utils/
      logging.py
      files.py

  mock_platform/
    main.py
    templates/
      login.html
      create_task.html
      success.html
      status.html
    static/

  dashboard/
    Home.py

  tests/
    test_import_service.py
    test_copy_schema.py
    test_copy_service.py
    test_task_state.py

  sample_data/
    sample_tasks.csv
    sample_video.mp4

  artifacts/
    screenshots/
    logs/

  docs/
    project_plan.md

  .env.example
  pyproject.toml
  README.md
```

当前状态：

- [x] ~~Phase 1 / Phase 2 所需的 `app/`、`tests/`、`sample_data/`、`artifacts/`、`docs/` 已建立。~~
- [x] ~~`mock_platform/` 目录存在，并已实现 Phase 3 页面和服务。~~
- [x] ~~`dashboard/` 目录存在，并已实现 Phase 4 页面。~~

## 5. 数据库表设计

`ad_tasks`

- [x] ~~`id`~~
- [x] ~~`video_path`~~
- [x] ~~`brand_name`~~
- [x] ~~`product_type`~~
- [x] ~~`selling_points`~~
- [x] ~~`target_audience`~~
- [x] ~~`platform`~~
- [x] ~~`copy_style`~~
- [x] ~~`template_id`~~
- [x] ~~`status`~~
- [x] ~~`retry_count`~~
- [x] ~~`error_message`~~
- [x] ~~`platform_job_id`~~
- [x] ~~`created_at`~~
- [x] ~~`updated_at`~~

`ad_copies`

- [x] ~~`id`~~
- [x] ~~`task_id`~~
- [x] ~~`title`~~
- [x] ~~`marketing_copy`~~
- [x] ~~`selling_point_list`~~
- [x] ~~`voiceover_script`~~
- [x] ~~`raw_llm_response`~~
- [x] ~~`created_at`~~

`automation_runs`

- [x] ~~表模型已定义。~~
- [x] ~~Phase 3 需要实际写入运行记录。~~
- [x] ~~Phase 3 需要写入 `started_at`、`finished_at`、`screenshot_path`、`log_path`、`error_message`。~~

## 6. 任务状态

第一版只使用：

```text
PENDING
COPY_GENERATING
COPY_GENERATED
COPY_FAILED
AUTOMATION_RUNNING
SUBMITTED
FAILED
```

状态语义：

- [x] ~~`PENDING`：CSV 导入后等待处理。~~
- [x] ~~`COPY_GENERATING`：正在生成文案。~~
- [x] ~~`COPY_GENERATED`：文案生成并通过结构化校验。~~
- [x] ~~`COPY_FAILED`：LLM 调用或结构化校验失败。~~
- [x] ~~`AUTOMATION_RUNNING`：Playwright 正在提交 mock 平台。~~
- [x] ~~`SUBMITTED`：已成功提交 mock 平台，并获得 `platform_job_id`。~~
- [x] ~~`FAILED`：自动化提交失败。~~

重试规则：

- [x] ~~不使用 `RETRYING` 作为长期状态。~~
- [x] ~~重试文案生成：递增 `retry_count`，重新进入 `COPY_GENERATING`。~~
- [x] ~~重试自动化提交：递增 `retry_count`，重新进入 `AUTOMATION_RUNNING`。~~
- [x] ~~每次失败更新 `error_message`。~~
- [x] ~~自动化失败额外保存截图和日志路径。~~

## 7. 核心任务流程

- [x] ~~用户上传 CSV。~~
- [x] ~~FastAPI 解析 CSV，为每行创建 `PENDING` 任务。~~
- [x] ~~用户触发文案生成。~~
- [x] ~~任务进入 `COPY_GENERATING`。~~
- [x] ~~`copy_service` 使用 LangChain prompt 调用 mock 或真实 LLM。~~
- [x] ~~Pydantic 校验成功后写入 `ad_copies`，任务进入 `COPY_GENERATED`。~~
- [x] ~~LLM 调用或校验失败时，任务进入 `COPY_FAILED`，记录 `error_message`。~~
- [x] ~~用户触发自动提交。~~
- [x] ~~任务进入 `AUTOMATION_RUNNING`。~~
- [x] ~~Playwright 操作 mock 平台完成登录、填写表单、选择模板、提交。~~
- [x] ~~提交成功后保存 `platform_job_id`，任务进入 `SUBMITTED`。~~
- [x] ~~自动化失败后保存错误、截图路径、日志路径，任务进入 `FAILED`。~~
- [x] ~~Dashboard 展示任务状态、生成文案、失败原因、截图路径、日志路径和重试入口。~~

## 8. 开发阶段与验收标准

### Phase 1：基础项目和 CSV 导入

- [x] ~~初始化 `ai-ad-video-automation/` 项目结构。~~
- [x] ~~建立 FastAPI、SQLite、SQLModel、配置和基础日志。~~
- [x] ~~实现 CSV 导入、任务列表、任务详情。~~
- [x] ~~实现简化状态枚举和状态流转工具。~~

验收标准：

- [x] ~~sample CSV 可以导入。~~
- [x] ~~数据库中出现 `PENDING` 任务。~~
- [x] ~~API 可以查询任务列表和详情。~~
- [x] ~~pytest 覆盖 CSV 导入、缺字段失败、初始状态正确、非法状态流转失败。~~

### Phase 2：LLM 文案生成

- [x] ~~定义广告文案 Pydantic schema。~~
- [x] ~~编写 prompt template。~~
- [x] ~~实现 `LLM_PROVIDER=mock`。~~
- [x] ~~实现 KIMI / OpenAI-compatible API 配置。~~
- [x] ~~真实 API 失败时写入 `COPY_FAILED`，不得自动 fallback 到 mock。~~

验收标准：

- [x] ~~mock LLM 可稳定生成合法结构化文案。~~
- [x] ~~Pydantic 校验失败会进入 `COPY_FAILED`。~~
- [x] ~~`COPY_GENERATING -> COPY_GENERATED` 状态流转正确。~~
- [x] ~~pytest 覆盖 copy schema、mock 输出、非法输出失败。~~
- [x] ~~pytest 覆盖真实 provider 缺 API key 时不 fallback。~~

### Phase 3：Mock 平台和 Playwright 自动化

- [x] ~~实现 mock 登录页、任务创建页、提交成功页。~~
- [x] ~~页面元素使用稳定 `data-testid`。~~
- [x] ~~实现 Playwright 登录、填写表单、提交、提取 `platform_job_id`。~~
- [x] ~~实现自动化提交 API。~~
- [x] ~~实现自动化重试 API。~~
- [x] ~~自动化失败时保存截图和日志路径。~~

验收标准：

- [x] ~~mock 平台可以手动完成一次任务提交。~~
- [x] ~~Playwright 可以对一条 `COPY_GENERATED` 任务完成提交。~~
- [x] ~~成功后任务进入 `SUBMITTED`，并写入 `platform_job_id`。~~
- [x] ~~失败后任务进入 `FAILED`，并记录错误、截图路径和日志路径。~~
- [x] ~~不要求 Playwright e2e pytest 阻塞 MVP，但需要有可重复的手动验证步骤。~~

### Phase 4：Dashboard 和演示打磨

- [x] ~~Streamlit 只通过 FastAPI API 操作任务。~~
- [x] ~~支持 CSV 上传、任务列表、任务详情、生成文案、自动提交、重试失败任务。~~
- [x] ~~README 补充运行命令、架构说明和面试演示脚本。~~
- [x] ~~optional：增加 Playwright e2e pytest，不阻塞 MVP。~~

验收标准：

- [x] ~~可以从 Dashboard 完成完整闭环。~~
- [x] ~~面试演示可以在 3 到 5 分钟内讲清楚。~~
- [x] ~~核心 pytest 全部通过。~~
- [x] ~~Playwright e2e 若暂不实现，README 明确说明手动验证步骤。~~

## 9. 技术风险与简化方案

- [x] ~~LLM 输出不稳定：用 Pydantic 严格校验；mock 模式保证演示稳定。~~
- [x] ~~真实 API 不可用：真实模式失败必须报错并记录原因，不静默 fallback。~~
- [x] ~~Playwright 选择器脆弱：mock 页面统一使用 `data-testid`。~~
- [x] ~~视频上传复杂：MVP 只模拟视频路径上传，不处理真实视频内容。~~
- [x] ~~后台任务复杂：第一版同步执行或使用 FastAPI `BackgroundTasks`，不引入 Celery。~~
- [x] ~~Dashboard 状态不一致：Dashboard 只调用 API，不直接读写数据库。~~
- [x] ~~Windows 路径兼容：代码中统一倾向使用 `pathlib.Path`。~~
- [x] ~~日志过重：第一版日志写到文件路径即可，不需要复杂日志检索系统。~~

## 10. 面试展示方式

推荐展示顺序：

- [x] ~~说明业务痛点：广告素材团队需要批量生成、填表、上传和追踪任务。~~
- [x] ~~展示系统架构：CSV 导入、LLM 文案生成、Pydantic 校验、Playwright 自动化、状态管理、Dashboard。~~
- [x] ~~导入 sample CSV，展示多条 `PENDING` 任务。~~
- [x] ~~触发文案生成，展示结构化广告标题、卖点、营销文案和口播脚本。~~
- [x] ~~触发自动提交，展示 Playwright 操作 mock 平台并返回 `platform_job_id`。~~
- [x] ~~展示失败任务的错误原因、截图路径、日志路径和 `retry_count`。~~
- [x] ~~总结亮点：这个项目不是做视频模型，而是把 AI 生成能力、结构化可靠性、自动化执行和任务追踪做成一个完整业务闭环。~~

## 11. 当前进度快照

- [x] ~~Phase 1 完成。~~
- [x] ~~Phase 2 完成。~~
- [x] ~~Phase 3 完成。~~
- [x] ~~Phase 4 完成。~~

最近一次已知测试命令：

```powershell
conda run -n learn-a pytest
```

最近一次已知结果：

```text
21 passed
```
