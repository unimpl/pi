"""Authored Chinese chapters. HTML is trusted author content, never user input."""

CHAPTERS = [
    {
        "slug": "foundations", "title": "先认识 Pi 的核心对象", "subtitle": "Session 保存工作，Agent 执行；一次 run 由一个或多个 turn 组成。", "level": "基础", "diagram": "concept",
        "intro": "先不要从“智能”开始。把 Pi 看成一组有包含关系和时间边界的普通对象：AgentSession 组织产品能力，SessionManager 保存会话记录，Agent 持有执行状态；用户发起一次 run，run 内包含一个或多个 turn，工具调用和结果通过消息连接。",
        "sections": [
            ("objects", "第一层：当前活动对象及其数量", """<table><thead><tr><th>Pi 对象</th><th>数量关系</th><th>它拥有或负责什么</th></tr></thead><tbody><tr><td><code>AgentSessionRuntime</code></td><td>CLI 通常有 1 个当前槽位</td><td>运行时容器，不是对话本身。持有当前 AgentSession 及与工作目录绑定的服务；切换会话时用新对象替换旧对象。</td></tr><tr><td><code>AgentSession</code></td><td>当前槽位中 1 个</td><td>应用协调层。持有 1 个 Agent、1 个 SessionManager 和设置、资源，把扩展、压缩、重试、模型切换等产品行为组织成统一 API。</td></tr><tr><td><code>SessionManager</code></td><td>每个 AgentSession 1 个</td><td>管理当前持久会话树；保存消息、模型切换、压缩摘要和扩展数据。</td></tr><tr><td><code>Agent</code></td><td>每个 AgentSession 1 个</td><td>执行内核。持有当前模型、工具、消息、队列、取消控制器和运行状态。</td></tr></tbody></table><p>如果写成 Go，<code>*Agent</code> 表示“指向一个 Agent”，不是多个 Agent。多个 Agent 通常会写成 <code>[]*Agent</code> 或 <code>map[ID]*Agent</code>；当前 AgentSession 的字段是单个 <code>agent: Agent</code>，没有 Agent 数组。</p><p>“协调层”不是 UI，也不是空包装。界面把 <code>prompt</code>、<code>abort</code>、<code>compact</code>、模型切换等操作交给 AgentSession；AgentSession 再调用 Agent，监听执行事件，通过 SessionManager 持久化，并运行扩展与恢复策略。这样，低层 Agent 不需要知道 CLI、会话文件或产品设置。</p><aside class="note"><strong>与行业术语的近似映射：</strong>可以先把 Pi 的 <code>Agent</code> 理解成 harness 的执行核心，把 <code>AgentSession</code> 理解成可供 CLI 使用的 agent 应用层，把整个 Pi CLI 理解成用户实际使用的 coding agent 产品。这个映射只是入门近似：行业里的 harness 往往还包括模型适配、上下文治理、权限与可观测性；Pi 将其中一些职责放在 <code>AgentSession</code> 或更外层。行业里的 “agent” 也没有统一的数据结构边界。</aside><p>判断边界时不要只看类名，要看职责：<code>Agent</code> 回答“下一次模型调用和工具循环怎样继续”，<code>AgentSession</code> 回答“这个产品会话怎样保存、配置、扩展、压缩和恢复”。</p><aside class="note"><strong>Runtime 不是另一个 session：</strong>它更像 Go 中的 <code>struct { current *AgentSession; services Services; factory Factory }</code>。<code>current</code> 才是用户当前操作的 AgentSession；Runtime 保存这个引用，并提供 <code>newSession</code>、<code>switchSession</code>、<code>fork</code> 和 <code>dispose</code> 等生命周期操作。</aside><p>为什么还要这一层？切换会话不只是换一份聊天记录。Pi 必须先终止当前执行，发送关闭事件，释放旧扩展，再根据目标会话的工作目录重建相关服务，最后把界面重新绑定到新 AgentSession。AgentSessionRuntime 把这套替换顺序集中起来，避免 CLI 各处分别实现。</p><p>启动一次 Pi CLI，通常只有一个当前活动的 AgentSession。磁盘上可以存在很多历史 session 文件，但它们不是同时塞在这个 AgentSession 里的多个 Agent。用户切换或恢复会话时，AgentSessionRuntime 会拆除当前运行对象，再创建并绑定新的 AgentSession。仓库的新 Harness API 属于另一条更通用、仍在演进的路径，第一遍不混入这里。</p>"""),
            ("run-turn", "第二层：run 与 turn 是时间边界", """<p><strong>run</strong> 不是长期对象，而是 Agent 对一次 <code>prompt()</code> 或 <code>continue()</code> 的执行生命周期。从 <code>agent_start</code> 开始，到 <code>agent_end</code> 事件的监听器全部完成后，Agent 才重新空闲。同一个 Agent 不允许并发启动两个 run；运行中追加输入要进入 steering 或 follow-up 队列。</p><p><strong>turn</strong> 可以先理解为“一次完整的模型请求与响应周期”，但它还包括该 assistant 响应触发的全部工具调用和工具结果。它从 <code>turn_start</code> 开始：把待处理消息放入上下文，请求一次模型并得到一条完整 assistant message；若其中有 toolCall，则执行工具并生成 toolResult；最后发送 <code>turn_end</code>。所以 turn 不是“一个 user message 加一个 assistant message”的对话对子。</p><p>如果第一个 turn 调用了 read，工具结果被追加进消息后，循环还要再次请求模型，让模型基于读取结果继续回答，于是同一个 run 进入第二个 turn。</p><p>因此关系是：一个 AgentSession 长期持有一个 Agent；Agent 在某个时刻最多运行一个 run；一个 run 包含一个或多个 turn。不要把“用户发了一条消息”“调用了一次模型”“完成了一次任务”都叫一轮。</p>"""),
            ("usage-trace", "把实际使用过程映射到对象", """<ol class="trace-list"><li><strong>启动 Pi：</strong><code>createAgentSession()</code> 创建当前活动的 AgentSession，并装配 Agent 与 SessionManager。默认是新会话；使用恢复、指定 session 等入口时，也可能加载已有记录。</li><li><strong>Pi 空闲时发送普通消息：</strong>文本先变成一条 role 为 user 的 AgentMessage，然后 <code>Agent.prompt()</code> 启动一次 run。</li><li><strong>模型直接回答：</strong>运行时请求模型一次，得到一条不含工具调用的 assistant message。这次请求与响应构成一个 turn，当前 run 随后结算。</li><li><strong>模型要求读取文件：</strong>第一个 turn 请求模型并得到含 read toolCall 的 assistant message，随后执行 read 并追加 toolResult；为了让模型看到结果，同一个 run 再进入第二个 turn并再次请求模型。它可以继续产生更多 turn。</li><li><strong>run 结束后再次输入：</strong>新的普通消息通常启动新的 run，但仍在同一个 AgentSession 和持久 session 中，因此会接着已有记录工作。</li></ol><pre><code>run\n├─ turn 1：请求模型 → assistant(toolCall: read) → 执行 read → toolResult\n└─ turn 2：携带 toolResult 请求模型 → assistant(最终文字回答)</code></pre><p>两个例外需要记住。第一，运行中输入的 steering 或 follow-up 会排队进入当前活动 run，不会并发启动另一个 run。第二，斜杠命令、本地 shell 等产品操作不一定经过模型，所以“界面里提交一次输入”不总是等于一次 Agent run。</p>"""),
            ("messages", "第三层：Message 是各层之间的共同记录", """<p><code>AgentState.messages</code> 是当前 transcript。基础角色包括 system、user、assistant 和 toolResult；coding-agent 还能增加只供应用使用的自定义消息，随后在模型请求边界转换或过滤。</p><p>以“解释 README”为例：system 保存规则和工具声明；user 保存目标；assistant 先返回一个 read toolCall；toolResult 带相同的 toolCallId 保存文件内容；第二个 assistant 才生成解释。assistant 消息因此不等于最终答案，它也可以是一次待执行的动作请求。</p><p>SessionManager 保存的范围更大：除了 message 条目，还有模型变更、thinking level、压缩摘要、分支摘要和扩展数据。模型真正看到的上下文只是从这些记录构建出的投影，不是整个 SessionManager。</p><aside class="note"><strong>session 文件不等于 AgentSession：</strong>AgentSession 是内存中的运行对象；JSONL 文件只是 SessionManager 管理的持久记录。恢复时，Pi 读取文件、构建当前分支的模型上下文，再创建新的 Agent 和 AgentSession。文件没有保存工具函数、事件监听器、取消控制器或正在流式生成的半条消息。</aside>"""),
            ("tools", "第四层：Tool 定义能力，toolCall 与 toolResult 记录一次使用", """<p><code>AgentTool</code> 是长期注册在 Agent 上的能力定义，包含名称、描述、参数 schema 和 <code>execute()</code>。它类似 Go 中带元数据的接口实现，或 Rust 中实现 trait 的值。</p><p><code>toolCall</code> 是某个 assistant 消息中的一次调用请求；<code>toolResult</code> 是执行后的消息。二者通过 toolCallId 关联。一次 assistant 响应可以对同一个工具发出多个调用，因此不能只用工具名配对。</p><p>toolCall ID 通常由模型服务的响应协议提供，Pi 的 provider 适配层读取后放进 <code>toolCall.id</code>。运行时执行工具后，把同一个值复制到 <code>toolResult.toolCallId</code>。它应被当作不透明的关联键，而不是带业务含义的 ID；某些 provider 不提供或重复提供 ID 时，Pi 的适配层会补生成唯一值。</p><p>模型只能产生 toolCall 数据。真正的文件读取发生在运行时查找工具、校验参数、通过策略钩子并调用 execute 之后。这个分离让宿主可以拒绝、取消、记录或替换副作用。</p>"""),
            ("model", "第五层：Model 与 StreamFn 位于 Agent 的外部边界", """<p><code>Model</code> 描述要调用的具体模型及其 provider、API、上下文窗口等能力；<code>StreamFn</code> 是 Agent loop 请求一次模型响应的函数契约。Agent 不直接依赖某家供应商客户端。</p><p>一次 turn 调用 StreamFn，消费响应事件并结算出完整 assistant 消息。流式事件只让界面逐步看到文本或工具参数；是否继续下一 turn，仍由完整响应、工具结果和队列状态共同决定。</p><p>对第一遍阅读而言，记住调用方向即可：AgentSession 组织产品策略；Agent 驱动 run；run 产生 turn；turn 通过 StreamFn 请求 Model，并通过 AgentTool 接触外部环境；产生的消息同时更新 Agent 状态并由 SessionManager 持久保存。</p>"""),
            ("priority", "先掌握关系，再读实现细节", """<p class="analysis">第一遍必须能回答五个问题：谁保存完整会话；谁持有当前执行状态；一次 run 何时开始和真正结束；为什么一个 run 会有多个 turn；toolCall 为什么不是工具已经执行。</p><details class="reference-answer"><summary>查看参考答案</summary><ol><li><strong>谁保存完整会话？</strong> <code>SessionManager</code> 管理完整的持久会话树，并在启用持久化时写入 JSONL。<code>AgentState.messages</code> 只保存当前 Agent 使用的 transcript，不代表包含所有分支和会话元数据。</li><li><strong>谁持有当前执行状态？</strong> <code>Agent</code> 持有 <code>AgentState</code> 及当前 active run，包括模型、工具、消息、流式中的 assistant message、待完成工具调用、队列和取消信号。AgentSession 负责协调产品策略，不直接实现底层循环。</li><li><strong>一次 run 何时开始和真正结束？</strong> 调用空闲 Agent 的 <code>prompt()</code> 或 <code>continue()</code> 后，Agent 先创建 active run 与 AbortController、设置 <code>isStreaming</code>，循环再发送 <code>agent_start</code>。<code>agent_end</code> 表示循环不再产生事件；只有它的异步监听器全部完成，<code>finishRun()</code> 清除 active run，并使 <code>waitForIdle()</code> 完成后，run 才真正结算。</li><li><strong>为什么一个 run 会有多个 turn？</strong> 一个 turn 只包含一次 assistant 响应及其工具结果。若响应要求调用工具，模型此时还没看到结果；运行时必须把 toolResult 加入上下文，再发起下一次模型请求，因此同一个 run 会进入下一个 turn。steering 和 follow-up 也可能让该 run 继续产生 turn。</li><li><strong>为什么 toolCall 不代表工具已经执行？</strong> toolCall 只是 provider 返回的结构化请求数据。运行时仍需查找工具、准备和校验参数、经过策略钩子，再调用 <code>execute()</code>。执行完成或失败后产生独立的 toolResult；只有 toolResult 才记录宿主实际得到的结果。</li></ol></details><p>现在可以忽略事件的全部变体、压缩算法、扩展钩子和多进程协议。它们都是在上述对象关系成立之后，为产品需求增加的机制。下一章再把这些对象放回包和模块边界中。</p>"""),
        ],
        "evidence": [("packages/coding-agent/src/core/sdk.ts", "const session = new AgentSession({", 16, "启动路径装配 AgentSession、Agent 与 SessionManager。"), ("packages/coding-agent/src/core/agent-session.ts", "export class AgentSession {", 18, "AgentSession 同时持有 Agent 与 SessionManager。"), ("packages/coding-agent/src/core/session-manager.ts", "export type SessionEntry =", 13, "持久会话不只保存消息，还保存配置变化、摘要和扩展数据。"), ("packages/agent/src/types.ts", "// Turn lifecycle", 4, "低层 turn 是一条 assistant 响应及其工具结果。"), ("packages/agent/src/types.ts", "export interface AgentTool<", 26, "AgentTool 是能力定义，execute 才产生真实副作用。"), ("packages/agent/src/agent.ts", "/** Start a new prompt", 20, "prompt 启动 run，同一 Agent 不允许并发运行。")],
    },
    {
        "slug": "architecture", "title": "沿着职责，而非目录理解架构", "subtitle": "把模型协议、执行机制与产品策略分开。", "level": "基础", "diagram": "architecture",
        "intro": "一个 monorepo 把多个包放在同一仓库，并不意味着每个请求都经过所有包。理解 pi 的第一步，是找到你正在研究的入口，再区分直接调用、包依赖与未来的组合方式。",
        "sections": [
            ("cli-main", "Pi CLI 的 TypeScript 主函数在哪里", """<p>仓库没有一个统管所有包的 <code>main()</code>，因为它是 monorepo。若问题指用户执行的 <code>pi</code> 命令，npm 包的 <code>bin</code> 字段把 <code>pi</code> 指向构建产物 <code>dist/bundle/cli.js</code>；对应的 TypeScript 源入口是 <code>packages/coding-agent/src/cli.ts</code>。</p><pre><code>#!/usr/bin/env node&#10;import { setupCli } from "./cli/setup.ts";&#10;import { main } from "./main.ts";&#10;&#10;setupCli();&#10;main(process.argv.slice(2));</code></pre><p><code>cli.ts</code> 是很薄的进程入口：先设置 CLI 进程环境，再把去掉 <code>node</code> 和脚本路径后的参数交给 <code>main()</code>。真正的 CLI 主函数位于 <code>packages/coding-agent/src/main.ts</code>：</p><pre><code>export async function main(args: string[], options?: MainOptions)</code></pre><p>它依次处理认证与包管理命令、解析参数、决定 interactive / print / RPC 模式、选择或创建 SessionManager、装配 AgentSessionRuntime，最后调用 <code>InteractiveMode.run()</code>、<code>runPrintMode()</code> 或 <code>runRpcMode()</code>。因此读 CLI 启动流程应从 <code>cli.ts → main.ts</code> 开始，再沿所选模式向下追踪。</p><aside class="note"><strong>不要和 npm 的 <code>main</code> 字段混淆：</strong><code>packages/coding-agent/package.json</code> 中的 <code>main: ./dist/index.js</code> 是别人 <code>import</code> 这个 SDK 时加载的库入口；<code>bin.pi</code> 才是执行 <code>pi</code> 命令的入口。SDK 用户直接调用 <code>createAgentSession()</code>，不会经过 CLI 的 <code>main()</code>。</aside>"""),
            ("entry", "从 SDK 的装配点出发", """<p><code>createAgentSession()</code> 是理解当前编程助手的好入口。它确定工作目录，准备模型运行时、设置、资源加载器和会话管理器，然后构造 Agent，最后构造 AgentSession。它是一个装配点：把各个部件接在一起，而不是独自实现推理、文件工具或终端绘制。</p><p>具体例子：恢复旧会话时，SDK 先从 SessionManager 建立已有上下文，再尝试恢复模型与 thinking level；模型不可用时形成回退说明。这个需求属于“用户如何继续工作”，因此放在产品装配层，而不塞进每次工具执行的低层循环。</p><p>图中箭头表示主要职责协作，不是完整 import 图。AgentSession 包装 Agent，Agent 调用循环，循环通过注入的 streamFn 接入模型。UI 消费事件；不能把 UI 画成模型生成之后必经的业务处理层。</p>"""),
            ("sdk-usage", "这几行代码已经在使用 Pi 吗", """<p><strong>是。</strong>这段代码把 Pi 当作库嵌入当前 Node.js 进程，创建一个没有 CLI 界面的 coding-agent 会话，并用 <code>session.prompt()</code> 启动一次完整 run。它使用的是与 Pi CLI 相同的核心装配与执行能力，但没有终端界面、交互命令和会话选择器。</p><table><thead><tr><th>代码</th><th>实际作用</th></tr></thead><tbody><tr><td><code>ModelRuntime.create()</code></td><td>加载模型目录、<code>~/.pi/agent/models.json</code> 与认证存储；后续仍需存在可用模型及其凭据。</td></tr><tr><td><code>SessionManager.inMemory()</code></td><td>创建只在进程内存在的会话记录；退出后不能恢复，也不会写 session JSONL。</td></tr><tr><td><code>createAgentSession(...)</code></td><td>装配资源加载器、设置、模型、默认工具、Agent 与 AgentSession。未指定 <code>cwd</code> 时使用 <code>process.cwd()</code>。</td></tr><tr><td><code>session.prompt(...)</code></td><td>把文本变成 user message，运行一个可能包含多个 turn 和工具调用的 run，并等待它真正结算。</td></tr></tbody></table><p><code>prompt()</code> 的返回类型是 <code>Promise&lt;void&gt;</code>。这里的 <code>await</code> 只表示“等本次 run 完成”，不会把最终文本作为字符串返回。要实时显示答案，应在调用前用 <code>session.subscribe()</code> 监听 <code>message_update</code>；只关心完成结果时，可以在 <code>await</code> 后查看 <code>session.messages</code>。SDK 文档的 Quick Start 因此比题目中的片段多了一段事件订阅。</p><pre><code>const stop = session.subscribe((event) =&gt; {&#10;  if (event.type === "message_update" &amp;&amp;&#10;      event.assistantMessageEvent.type === "text_delta") {&#10;    process.stdout.write(event.assistantMessageEvent.delta);&#10;  }&#10;});&#10;&#10;await session.prompt("What files are in the current directory?");&#10;stop();&#10;session.dispose();</code></pre><p>若没有显式设置 <code>tools</code>，当前默认内置工具是 <code>read</code>、<code>bash</code>、<code>edit</code>、<code>write</code>。所以问题里的 prompt 不只是“问模型”：模型可以提出工具调用，由本地进程以当前用户权限执行，再把 toolResult 送回下一 turn。只做只读集成时，应显式选择 <code>tools: ["read", "grep", "find", "ls"]</code>。</p><aside class="note"><strong>它创建了什么？</strong>创建的是一个 <code>AgentSession</code> 对象，其中持有一个 <code>Agent</code> 和一个内存型 <code>SessionManager</code>。这不是启动一个后台 Pi CLI 进程，也不是每次 <code>prompt()</code> 都新建 AgentSession；多次调用 <code>prompt()</code> 会在同一会话中继续已有消息。</aside>"""),
            ("boundaries", "三个核心边界", """<table><thead><tr><th>模块</th><th>概念别名</th><th>拥有的责任</th><th>不应从它期待什么</th></tr></thead><tbody><tr><td>pi-ai</td><td>Model Runtime / Model API</td><td>模型描述、统一消息、provider 适配、响应事件</td><td>替用户决定项目任务或管理 CLI 交互</td></tr><tr><td>pi-agent-core</td><td>Agent Core / Agent Runtime</td><td>基础 Agent、工具循环、队列；也导出更高阶 Harness/Session 能力</td><td>所有导出都只是一个小循环</td></tr><tr><td>pi-coding-agent</td><td>Application / Product Shell</td><td>SDK 装配、会话策略、具体工具、扩展和运行模式</td><td>天然获得进程隔离或文件权限沙箱</td></tr><tr><td>pi-tui</td><td>Presentation</td><td>终端组件与显示能力</td><td>决定模型是否继续调用工具</td></tr></tbody></table><p>注意 pi-agent-core 已经不只包含 agent-loop.ts。先读低层内核，是学习顺序，不是对包规模的描述。后面的进阶章节才引入 Harness 与存储契约。</p>"""),
            ("package-map", "packages 下每个目录负责什么", """<p>这些目录是可独立构建和发布的 npm workspace 包，不是一次请求依次经过的流水线。下面按当前公开职责和学习优先级定位：</p><table><thead><tr><th>目录</th><th>职责</th><th>第一遍优先级</th></tr></thead><tbody><tr><td><code>coding-agent</code></td><td>完整 Pi coding agent 产品：CLI/SDK 入口、AgentSession、JSONL 会话、内置文件与 shell 工具、扩展、技能、压缩，以及 interactive/print/JSON/RPC 模式。</td><td><strong>主入口</strong></td></tr><tr><td><code>agent</code></td><td>通用执行内核：Agent 状态、模型—工具循环、事件、steering/follow-up；当前还包含更通用的 Harness、Session 与存储契约。</td><td><strong>核心</strong></td></tr><tr><td><code>ai</code></td><td>统一 LLM API：Model、消息与流事件类型、provider 适配、认证解析、模型目录、用量与费用。它负责“怎样调用模型”，不负责完成 coding task。</td><td><strong>核心</strong></td></tr><tr><td><code>tui</code></td><td>通用终端 UI 库：输入编辑器、Markdown、列表、布局、键盘与鼠标、差量渲染和终端图片。它显示和收集输入，不决定 Agent 循环。</td><td>读界面时再看</td></tr><tr><td><code>session-backends</code></td><td>pi-agent-core 新 Session 接口的可选存储实现；当前子包 <code>sqlite-node</code> 用 Node 的 SQLite 保存 Session。它不是 coding-agent 现有 JSONL SessionManager 的同义目录。</td><td>进阶存储</td></tr><tr><td><code>chord</code></td><td>独立的应用组合运行时：用 plugin/facet、类型化 service、复制状态和远程服务边界组合多个运行环境。它可服务 Pi，也可用于无关应用。</td><td>进阶架构</td></tr><tr><td><code>protocol</code></td><td>实验性远程协议：定义 CBOR 帧、请求关联、取消、订阅和 server/session/attachment 路由信封，不解释 Agent 业务数据。</td><td>可先忽略</td></tr><tr><td><code>client</code></td><td>实验性远程客户端：在任意有序字节传输之上连接 server、发送请求、订阅服务状态并管理 attachment 路由。</td><td>可先忽略</td></tr><tr><td><code>server</code></td><td>实验性本地服务端：把远程连接路由到 Session 和 Chord service，管理多展示端 attachment；不是模型 provider 服务。</td><td>可先忽略</td></tr><tr><td><code>durable</code></td><td>面向持久 conversation/task/document 的 Pico 方向。当前公开 API 主要是持久记录契约和脱离 Agent 的内存存储，设计文档多于完整运行时实现。</td><td>了解问题即可</td></tr><tr><td><code>telemetry</code></td><td>与厂商无关的观测契约：span、attribute、event、schema 和内存参考实现；不自带 OpenTelemetry/Sentry exporter，也不控制业务流程。</td><td>工程化阶段</td></tr><tr><td><code>evals</code></td><td>Pi coding agent 的行为评估工程：组织测试案例、容器隔离、重复运行和结果比较，用于衡量行为或文档带来的效果。</td><td>评估阶段</td></tr></tbody></table><p><strong>第一次源码阅读顺序：</strong><code>coding-agent/src/cli.ts → main.ts → core/agent-session.ts → agent/src/agent.ts → agent-loop.ts → ai</code> 中实际使用的 provider。若目标是自己实现第一个 harness，到这里已经足够；先不要从 Chord、远程协议或 Durable 开始。</p><p class="analysis">设计判断：拆包的主要价值是让模型适配、执行循环、产品策略和 UI 可以独立变化及复用。代价是概念会分散到多个 package，仓库结构也混合了当前主路径与演进中的新能力，因此必须从入口追踪实际调用，不能只按目录名猜架构。</p>"""),
            ("minimal-scope", "最小复刻时只看 agent 和 ai 吗", """<p><strong>若目标是最小 Agent 执行内核，基本可以。</strong><code>ai</code> 提供模型、消息、工具调用和响应流的协议；<code>agent</code> 在其上实现“请求模型 → 执行工具 → 追加 toolResult → 再请求模型”的循环、运行状态和事件。</p><p>但这两个包不会自动变成一个可操作的 coding agent。你仍需写一个很薄的宿主层：选择模型和凭据，定义 system prompt，注册至少一个工具，接收用户输入，订阅输出，并在结束时释放资源。这个宿主层在职责上相当于 <code>coding-agent</code> 的极小子集，不需要复制 AgentSession 的全部压缩、扩展、恢复和 UI 能力。</p><table><thead><tr><th>第一遍读取</th><th>理解目标</th></tr></thead><tbody><tr><td><code>agent/src/types.ts</code></td><td>AgentMessage、AgentTool、事件以及 run/turn 数据契约</td></tr><tr><td><code>agent/src/agent.ts</code></td><td>Agent 如何持有状态、启动 run、排队输入和取消</td></tr><tr><td><code>agent/src/agent-loop.ts</code></td><td>模型与工具循环如何推进和停止</td></tr><tr><td><code>agent/src/stream-fn.ts</code></td><td>执行内核如何注入一次模型调用</td></tr><tr><td><code>ai/src/types.ts</code></td><td>Model、Context、toolCall/toolResult 和流事件</td></tr><tr><td><code>ai</code> 中一个 provider/API</td><td>统一协议怎样落到一家真实模型服务</td></tr></tbody></table><p>现在可以忽略 <code>agent/src/harness/</code> 下更高阶的 Session、持久化与资源抽象，也可以忽略 coding-agent 的 JSONL、压缩、技能、扩展、TUI、Chord 和远程协议。等最小非持久循环成立后，再按真实需求加入取消、会话保存和上下文预算。</p><aside class="note"><strong>“只关心”指学习范围，不一定指 npm 依赖图。</strong>当前 <code>pi-agent-core</code> 包本身声明了 Chord 和 telemetry 等依赖；直接安装它时包管理器会处理这些传递依赖。你不需要为了理解最小 agent loop 先阅读它们。</aside>"""),
            ("naming", "Agent Core、Runtime 与 Harness 的边界", """<p><code>agent</code> 和 <code>ai</code> 是仓库中的实际目录名，但设计自己的系统时不必照抄。<code>agent</code> 的公开 npm 名称已经是 <code>pi-agent-core</code>；称为 <strong>Agent Core</strong> 或 <strong>Agent Runtime</strong> 能更准确表达它持有状态并推进执行。单独称为 <code>core</code> 又过于宽泛，离开项目上下文后看不出是哪一种核心。</p><p><strong>Harness 通常比 Agent Core 更大。</strong>Core/Runner 回答“下一 turn 怎样执行”；Harness 回答“模型在什么受控环境中长期工作”。后者通常进一步拥有工具与资源装配、system prompt、上下文预算、会话持久化、恢复、权限、观测和扩展机制。</p><table><thead><tr><th>层</th><th>Pi 中的近似位置</th><th>核心问题</th></tr></thead><tbody><tr><td>Agent Core / Runner</td><td><code>agent.ts</code>、<code>agent-loop.ts</code></td><td>一次 run/turn 如何推进、执行工具和停止？</td></tr><tr><td>Agent Harness</td><td><code>agent/src/harness/</code></td><td>如何把循环、Session、资源、压缩、技能和恢复组织成通用运行环境？</td></tr><tr><td>Coding Harness / Product</td><td><code>coding-agent</code></td><td>如何把这些能力变成带 CLI、具体工具、设置和扩展的编码产品？</td></tr></tbody></table><p>因此，如果你的模块只有模型—工具循环，叫 <code>agent-core</code>、<code>agent-runtime</code> 或 <code>runner</code> 更诚实；当它开始统一管理工具、上下文、会话和生命周期时，叫 <code>harness</code> 更合适。Pi 的 README 将完整 coding-agent 称为 “terminal coding harness”，而仓库也已经存在独立的 <code>AgentHarness</code> 接口，正好体现这一级差异。</p><p><code>ai</code> 确实偏宽。它不只包含 OpenAI、Anthropic 等 provider，还拥有统一 Model、消息、上下文、流事件、认证、目录和用量，因此整个包称为 <code>provider</code> 会缩小其真实职责。更准确的顶层名可以是 <strong>Model Runtime</strong>、<strong>Model API</strong> 或 <strong>LLM</strong>，再把具体适配实现放进 <code>providers/</code>。</p><pre><code>agent-core/                 Agent 状态与执行循环&#10;harness/                    工具、上下文、Session 与运行策略&#10;model/                      统一模型契约与调用入口&#10;model/providers/openai/     具体供应商适配&#10;app/                        CLI 或其他产品交互</code></pre><p>命名的判断标准不是“听起来底层”，而是包名能否说明它隔离哪种变化：Agent 循环随控制策略变化，Harness 随运行治理需求变化，Model 层随模型协议变化，provider 子层随供应商 API 变化，app 层随产品需求变化。</p>"""),
            ("injection", "依赖注入落实在普通函数上", """<p>核心循环需要“获取一次模型响应”的能力，而不是某家供应商的全局单例。<code>StreamFn</code> 就是这个能力的函数契约。SDK 注入的实现调用 modelRuntime，并把超时、重试配置、请求头扩展等设置接进去。</p><p>对 Go 读者，可以类比构造函数接收一个 client 接口；对 C++ 读者，可以类比注入 callable。pi 这里不需要额外的依赖注入容器。收益是测试可提供模拟事件流，调用者可替换模型接入。代价是函数签名之外还有协议约束：返回流必须以正确的完成或错误事件结算。</p><p>当前代码同时保留 <code>setDefaultStreamFn()</code>：SDK 为旧消费者安装默认实现。它说明现实工程并非总是完全显式注入。这个进程级默认值便于兼容，但会引入初始化顺序和共享状态；不能把 pi 描述成“没有任何全局状态”。</p>"""),
            ("policies", "机制与策略：一个有用但不绝对的分界", """<p>循环提供 transformContext、beforeToolCall、prepareNextTurn 等接入点；宿主决定什么时候压缩、注册哪些工具、如何响应扩展。这体现了“提供机制，允许上层配置策略”。但循环仍有默认并行执行、错误转换和退出条件，它不是完全中性的空壳。</p><p class="analysis">分析推断：这一分层降低了更换模型或界面时重写控制逻辑的成本。代价是调用链跨文件，初读时不如一个大函数直观。读者应追踪“接口由谁实现、由谁调用”，而不是试图按目录顺序读完仓库。</p>"""),
            ("map", "给演进中的模块一个正确位置", """<p>Chord 提供独立的服务、插件与状态复制能力；protocol、client、server 的 README 明确标注实验性；Durable 的公开入口目前导出存储契约与 MemoryStorage。这些都值得学习，但不能由包名推导出“当前 CLI 已经完全运行在这套新架构上”。</p><p>本书基础路线研究 SDK 中可见的 Agent/AgentSession 装配，进阶路线研究新模块公开契约和文档。两条路线相连，但证据等级分别标注。未来代码变动时，先重新检查入口和导出，再修改架构图。</p>"""),
        ],
        "evidence": [("package.json", '"workspaces": [', 16, "根配置声明 packages 下的独立 npm workspaces。"), ("packages/agent/README.md", "Stateful agent with tool execution", 12, "agent 包公开定位是有状态执行、工具与事件流。"), ("packages/ai/README.md", "Unified LLM API", 10, "ai 包公开定位是统一模型 API 与 provider 能力。"), ("packages/coding-agent/src/cli.ts", "main(process.argv.slice(2));", 7, "pi 命令的 TypeScript 进程入口把参数交给 main。"), ("packages/coding-agent/src/main.ts", "export async function main", 18, "CLI 主函数负责启动准备、运行时装配和模式分派。"), ("packages/coding-agent/src/core/sdk.ts", "export async function createAgentSession(", 20, "SDK 是装配点，准备模型、设置与会话资源。"), ("packages/coding-agent/src/core/agent-session.ts", "async prompt(text: string", 22, "prompt 校验模型与凭据，构造 user message，并等待完整 Agent run。"), ("packages/coding-agent/src/core/sdk.ts", "const defaultActiveToolNames", 12, "未指定 tools 时启用 read、bash、edit、write。"), ("packages/coding-agent/src/core/sdk.ts", "agent = new Agent({", 18, "产品层向 Agent 注入模型调用实现。"), ("packages/agent/src/stream-fn.ts", "let defaultStreamFn", 19, "默认函数是当前仍存在的共享状态。"), ("packages/durable/src/index.ts", "export { MemoryStorage }", 25, "Durable 的实际公开导出，不能用设计文档代替。")],
    },
    {
        "slug": "journey", "title": "一次请求，究竟经过了什么", "subtitle": "跟随消息，而不是跟随屏幕上的文字。", "level": "核心", "diagram": "journey",
        "intro": "以“读取 README.md 并解释项目”为例。下面的轨迹是根据低层循环整理的教学演示，文件内容与模型回答是示例，不访问文件、不请求真实模型。",
        "sections": [
            ("input", "输入：先成为有角色的消息", """<p>Agent.prompt 接收字符串或消息。字符串会被包装为 user 消息；Agent 为本次运行建立取消控制器，并拒绝同一实例同时启动第二个 prompt。正在运行时的新输入应走 steer 或 followUp 队列。</p><p>runAgentLoop 把新消息接到已有上下文后面，发送 agent_start、turn_start 和相应消息事件。开始请求前还会对比当前可执行工具与历史中的工具声明，把变更写成 system 消息。这解决了“模型以为工具存在，但宿主已经换掉工具集合”的不一致。</p>"""),
            ("boundary", "请求边界：先变换，再转换", """<p>streamAssistantResponse 先执行 <code>transformContext</code>，仍在 AgentMessage 世界里操作；随后执行 <code>convertToLlm</code>，转换为模型支持的 Message；最后 normalizeContext 形成标准请求上下文，再调用 streamFn。</p><p>为什么分两步？应用可能有 bashExecution、压缩摘要、通知等消息。调整上下文时需要理解应用语义，而 API 适配时只应面对约定好的模型消息。若把两件事合成一个到处特殊判断的序列化函数，UI 特有数据容易泄漏到模型协议。</p><p>SDK 的 convertToLlm 还会根据 blockImages 设置过滤图片。这说明“本地记录了什么”和“这次允许发什么”是两个决策。模型请求边界正是统一实施这类转换的位置。</p>"""),
            ("response", "响应：先收齐工具调用，再执行", """<p>模型流先产生 start，随后产生 text、thinking 或 toolcall 的增量事件。循环更新当前部分消息并发出 message_update，最终使用 response.result() 的结果结算完整消息。流式工具参数尚未收齐时，不会在每个增量上直接执行工具。</p><p>示例中，最终 assistant 内容包含 read 调用。循环提取 toolCall，执行工具批次。read 返回内容后，运行时生成带 toolCallId 的 toolResult，把结果接到上下文，再进入下一轮模型请求。调用 ID 是结果与请求的关联键，不能只用工具名配对：一次响应可能两次调用同名工具。</p>"""),
            ("ending", "结束：无工具可做，也没有待处理消息", """<p>第二次模型响应给出解释，没有工具调用。循环还要检查 steering 与 follow-up 消息；都没有时才发送 agent_end。若 shouldStopAfterTurn 要求停止，会在当前 turn 完成后提前退出；模型 error 或 aborted 也有明确的终止路径。</p><p><strong>agent_end 不是“所有监听器已经完成”。</strong> Agent 类会等待事件订阅者，然后 finishRun 才清除运行状态。日志写入或会话保存若属于被等待的监听工作，也在这次运行的结算边界内。这一细节直接影响下一次 prompt 何时能安全开始。</p>"""),
            ("tradeoff", "为什么不让模型直接拿文件系统", """<p class="analysis">分析推断：显式的工具请求与结果保留了执行边界，使宿主能验证、记录、拦截和替换操作。代价是每次工具反馈通常需要下一轮模型调用，增加延迟和上下文占用。它适合需要依据外部结果逐步决策的任务；固定业务流程不必为了“Agent”这个名字把每一步都交给模型选择。</p><p>另一个代价是上下文增长。读取大文件会把大量结果带回模型，产品层因此需要截断、分段读取和压缩等策略。基础循环负责传递结果，结果应该多大则由具体工具和应用共同承担。</p>"""),
        ],
        "evidence": [("packages/agent/src/agent.ts", "private normalizePromptInput(", 23, "文本输入变成 user 消息。"), ("packages/agent/src/agent-loop.ts", "// Apply context transform", 19, "上下文变换、消息转换与模型调用的顺序。"), ("packages/agent/src/agent-loop.ts", "const toolCalls = message.content.filter", 27, "响应完成之后执行工具，并把结果追加到上下文。"), ("packages/agent/src/agent.ts", "private finishRun():", 9, "运行结算清理在事件处理完成后发生。")],
    },
    {
        "slug": "control", "title": "控制权必须留在运行时", "subtitle": "循环、队列与事件共同定义“什么时候能继续”。", "level": "核心", "diagram": "control",
        "intro": "如果用户在工具执行期间补充要求，立即修改正在运行的操作会产生什么后果？如果 UI 显示“完成”，会话还没保存呢？控制设计处理的正是这些时间边界。",
        "sections": [
            ("loops", "两层循环表达两种继续", """<p>内层循环处理工具反馈与 steering；外层循环处理 Agent 原本要停下时的 follow-up。它们代表不同意图：steering 是“下一轮请改变方向”，follow-up 是“当前工作结束后再做这件事”。</p><p>例子：模型一次请求读取 A、B 两个文件。读取期间用户说“重点看 B”。steering 不会跳过这批已提出的调用，而是在当前 turn 的工具执行完成后注入。若用户发的是“解释完再写摘要”，follow-up 会等到当前循环无工具和 steering 时才进入。</p><p>两类队列可按一次一条或一次全部排空。把输入分开是额外 API 复杂度，却避免了所有消息只有一种抢占语义。不要把 steer 翻译成“立即中断当前工具”。</p>"""),
            ("operations", "在 Pi 界面中如何触发", """<table><thead><tr><th>操作</th><th>运行中提交时</th><th>何时进入模型上下文</th></tr></thead><tbody><tr><td>普通 Enter</td><td>作为 steering 排队</td><td>当前 assistant 响应及其工具批次结束后，在下一次模型调用前</td></tr><tr><td>follow-up 快捷键</td><td>作为 follow-up 排队；macOS/Linux 默认 Alt+Enter，Windows 默认 Ctrl+Q，按键可配置</td><td>当前工作已经没有工具续轮和 steering、本来将要结束时</td></tr></tbody></table><p>因此你的理解基本正确：它们通常都是“上一次 run 还没结束时，用户又发了一条消息”。区别不在消息内容，而在排队语义。</p><p>steering 也不是立即打断当前 turn。模型正在流式生成时，它不会终止这次请求；工具正在执行时，它也不会撤销这批工具。它会等待当前 turn 完整结算，然后作为新的 user message 进入下一 turn。真正要停止当前模型或工具，应使用 interrupt/abort。</p><p>follow-up 表达“先完成当前任务，再做这件事”。例如当前目标是修复错误，follow-up 可以是“完成后再写一段变更摘要”。在低层循环中，它会在 Agent 原本准备发出 agent_end 的位置被取出，使活动 run 继续产生后续 turn。</p><h3>Follow-up 与新 run 的真正区别</h3><table><thead><tr><th>边界</th><th>Follow-up</th><th>新 run</th></tr></thead><tbody><tr><td>提交时机</td><td>当前 run 仍活动时预先排队</td><td>通常在上一个 run 已完全结算、Agent 空闲后提交</td></tr><tr><td>agent_end</td><td>循环发现 follow-up 后暂不发送 agent_end</td><td>上一个 run 已发送 agent_end，且等待型监听器已经完成</td></tr><tr><td>生命周期</td><td>继续使用当前 run 的取消信号与运行边界</td><td>发出新的 agent_start，建立新的 run 生命周期</td></tr><tr><td>产品预处理</td><td>输入处理和模板展开已在排队时完成；不会完整重走一次空闲态 prompt 的启动流程</td><td>重新执行鉴权、压缩检查、before_agent_start、工具与系统提示准备等 run 级流程</td></tr></tbody></table><p><strong>模型是否看到不同提示词？不一定。</strong>run 边界本身不会被编码成一条消息。若两条路径最终具有相同的 system 内容、历史消息、新 user message、工具声明、模型和上下文转换结果，那么发送给 provider 的 transcript 可以等价，模型不会知道这是 follow-up 还是新 run。</p><p>输入会在这些情况下不同：新 run 的 <code>before_agent_start</code> 扩展增加了消息或修改系统提示；两次 run 之间切换了模型或工具；空闲态 prompt 的预检查触发压缩；等待期间积累的 bash 或自定义消息被写入上下文。follow-up 的下一 turn 也会执行 turn 级上下文刷新和阈值压缩，所以不能简单理解为“follow-up 不压缩，新 run 才压缩”。</p><p>因此 follow-up 的核心价值是调度，而不是一种特殊推理模式：用户可以在 Agent 忙碌时预先声明下一件事，运行时保证它排在当前任务之后并自动继续。若你需要先观察结果再决定下一步，应该等待并发送新 run；若下一步与结果无关，可以提前排为 follow-up。</p>"""),
            ("events", "事件既用于观察，也可能形成等待边界", """<p>Agent 的 processEvents 先更新内部状态，再按订阅顺序 await 每个 listener。监听者看到的是已更新的状态，监听 Promise 的完成也参与当前运行的完成。这可以让某些保存工作成为继续执行前的屏障。</p><p>低层 agentLoop 返回 EventStream，它推送事件而不等待外部异步迭代消费者处理完毕。两种 API 都产生事件，但等待语义不同。类比 Go：往一个队列发送任务，不等于等待接收者处理完；显式等待回调又是另一种契约。</p><p class="analysis">分析推断：可等待监听器有利于顺序一致性，但慢监听器会拖慢主流程，抛出异常还会影响结算。事件驱动不自动意味着彻底解耦，必须问清“生产者等待谁”。</p>"""),
            ("cancel", "取消是协作协议，不是事务回滚", """<p>Agent.abort 调用 AbortController.abort。信号继续传到模型调用、工具与钩子；这些实现必须配合检查或取消 I/O。它不是操作系统强杀线程，也不会撤销已经写入的文件。</p><p>比如文件写入已经交给底层系统，用户此刻取消，写入仍可能完成。file-mutation-queue 的测试专门覆盖“取消后的写入尚未结束时，后续写入不能抢先进入”。因此取消、I/O 完成和锁释放是三个不同时间点。</p><p>Go 的 context cancellation 是更接近的类比；Rust 的 drop future 不能直接当成相同语义，因为 JS Promise 本身不会因你不再等待就自动取消底层工作。</p>"""),
            ("errors", "区分工具失败和模型失败", """<table><thead><tr><th>情形</th><th>低层行为</th><th>设计意义</th></tr></thead><tbody><tr><td>工具不存在、参数不合法、执行抛错</td><td>生成 isError 工具结果，通常允许模型继续</td><td>把可解释的环境反馈带回决策者</td></tr><tr><td>模型 stopReason 为 error / aborted</td><td>结束 turn 和当前 loop</td><td>没有可靠响应时停止推进</td></tr><tr><td>响应达到 length 且含工具调用</td><td>整批调用记为失败，不实际执行</td><td>避免执行看似可解析、实际不完整的参数</td></tr><tr><td>工具批次全部 terminate</td><td>不因该批工具自动续轮；队列仍可要求继续</td><td>批次终止提示与队列策略分开</td></tr></tbody></table><p>工具错误不保证模型能恢复；模型可能继续重复失败。基础循环本身没有固定的最大轮数守卫。宿主可以用停止钩子建立预算或策略，不能将没有内置限制误读为“必然收敛”。</p>"""),
            ("style", "设计风格：显式顺序优于隐藏魔法", """<p class="analysis">分析推断：runLoop 用普通 while、条件分支与 await 表达顺序，读者能直接找到“何时注入输入”“何时退出”。与通用工作流图引擎相比，它更容易跟踪；当生命周期选项逐渐变多，嵌套分支也会增加理解成本。</p><p>值得借鉴的是明确边界与不变量，而不是照搬两层循环的语法。需要持久化恢复时，内存循环并不足够，必须额外记录已接受工作与外部效果；这正是进阶模块需要解决的问题。</p>"""),
        ],
        "evidence": [("packages/coding-agent/src/core/agent-session.ts", "async steer(text:", 24, "AgentSession 明确记录 steering 与 follow-up 的交付时机。"), ("packages/agent/src/agent-loop.ts", "// Outer loop:", 12, "两层循环对应不同的继续条件。"), ("packages/agent/src/agent-loop.ts", "// Agent would stop here.", 13, "follow-up 只在原本会停止的位置消费。"), ("packages/agent/src/agent.ts", "for (const listener of this.listeners)", 4, "类级订阅者按序等待。"), ("packages/ai/src/utils/event-stream.ts", "push(event: T): void", 17, "低层事件流的 push 不等待消费者。"), ("packages/coding-agent/test/file-mutation-queue.test.ts", 'it("keeps write queue locked', 14, "已有测试覆盖取消与未完成写入之间的边界；本书不声称已执行该测试。")],
    },
    {
        "slug": "models", "title": "统一模型接口，但保留差异", "subtitle": "抽象的目标是隔离变化，不是假装所有服务都一样。", "level": "核心", "diagram": "models",
        "intro": "不同模型 API 的消息格式、工具参数、推理选项和停止原因不同。如果这些分支散落在 Agent 循环里，增加一个供应商就可能破坏所有调用路径。pi 把变化集中到模型与 API 边界。",
        "sections": [
            ("contract", "先统一运行时需要的最小语言", """<p>Agent 主要需要四种消息角色，以及文本、图片、thinking、toolCall 等内容块。pi-ai 用类型表达这些数据，再用 AssistantMessageEvent 表达逐步生成过程。上层不必知道供应商在线路上如何拼装每个增量。</p><p><code>Model</code> 同时携带 id、provider、api、contextWindow、maxTokens 等元数据。provider 表示模型服务来源，api 表示协议实现，它们不是同一个维度。一个服务来源可能使用兼容别家的 API，所以不能只凭供应商名推断请求形状。</p><p>真实源码保留 responseId、thoughtSignature、thinkingSignature 等供应商相关字段。它们让多轮调用能够保存必要的关联或不透明数据。统一接口不等于把所有额外字段都丢掉。</p>"""),
            ("normalize", "在边界规范化，减少内部组合数", """<p>公开 Context 允许 systemPrompt、tools 这些便利字段；规范化之后的 TranscriptContext 则把规则与工具放进 system 消息。后续 system 消息能改变规则段落和工具集合，重放这些更新得到当前状态。</p><p>想象两条历史：早期允许 read，后来又加入 write。如果只有一个当前 tools 数组，单看消息很难解释当时模型为什么选择某个工具。把声明变化锚定在对话里，提高了记录的可解释性。运行时仍保留可执行工具对象，因为函数不能作为协议声明发送。</p><p>TranscriptContext 使用一个类型标记，防止普通 Context 被随意当成规范化结果传给适配器。它是编译期约束，不是加密校验，也不会自动验证任意外部 JSON。</p>"""),
            ("differences", "用能力与兼容信息承认差异", """<p>类型中有 ApiOptionsMap、按 API 选择的 compat 配置，以及 reasoning、thinkingLevelMap 等模型描述。某个模型不支持的参数，不能仅因为统一接口里存在就认为一定有效。SDK 还会按模型能力约束 thinking level。</p><p>比如有的 API 不接受对话中途的 system 消息，适配层需要将规则变化折叠到开头；另一些允许原位表达。保持内部 transcript 统一，把转换责任放在边界，比让 Agent 针对每种 API 写循环分支更容易维护。</p><p class="analysis">分析推断：代价是兼容选项会增长，统一数据也可能携带少数供应商才理解的字段。这是有意识的折中：保留表达能力，而非追求形式上最小的类型。</p>"""),
            ("errors", "流是一份协议，不只是一串 token", """<p>正常流有 start、增量、done；初始化失败可以直接产生 error。最终 AssistantMessage 带 stopReason、usage 和可能的 errorMessage。上层能用同一个结算入口读取完整结果，又能按事件更新界面。</p><p>接口之间仍有重要差别：Agent 的 StreamFn 契约要求运行失败在流中表达；pi-ai 的类型注释说明直接 streamSimple 在缺少认证时可能同步抛错。宿主桥接时必须理解这个差异，不能只看函数返回类型。</p><p>事件中的 partial 是活的累积响应，并非历史快照。保存引用再等待，看到的可能已经改变。对习惯 Rust 借用规则的读者，这提醒你：TypeScript 的 readonly 或类型注释无法替代运行时所有权隔离。</p>"""),
            ("tradeoff", "该学什么，不该神化什么", """<p>值得学习的是“稳定上层契约 + 明确转换边界 + 保留必要差异”。适配层降低更换供应商的代码成本，但不会消除模型行为差异、参数语义差异或能力差异。</p><p>阅读路线是先看消息和 StreamFn，再看 SDK 注入，最后挑一个 provider 工厂。第一遍不需要读完每家 API，也不要从巨大的生成模型目录开始。</p>"""),
        ],
        "evidence": [("packages/ai/src/types.ts", "export type TranscriptContext =", 5, "规范化的模型上下文具有类型标记。"), ("packages/ai/src/types.ts", "export interface Model<TApi", 20, "模型身份、协议和能力是独立字段。"), ("packages/ai/src/providers/openai.ts", "export function openaiProvider", 10, "Provider 工厂组合认证、模型目录和 API 实现。"), ("packages/agent/src/types.ts", "export type StreamFn =", 5, "循环只依赖流函数契约。"), ("packages/ai/src/types.ts", "* `partial` is the shared", 7, "partial 的可变语义在接口文档中明示。")],
    },
    {
        "slug": "tools", "title": "工具是能力，也是边界", "subtitle": "从声明到副作用，中间不能少掉执行规则。", "level": "核心", "diagram": "tools",
        "intro": "模型返回的工具调用来自外部生成，不是你在编译期写好的函数调用。pi 将声明、参数准备、校验、拦截、执行和结果结算拆开，使能力既能扩展，也能被宿主管理。",
        "sections": [
            ("declaration", "给模型的声明，给宿主的函数", """<p>Tool 描述 name、description、parameters；AgentTool 在此基础上增加 execute、label、执行模式等成员。模型依靠声明选择工具和形成参数，宿主靠 execute 完成真正的操作。把函数和描述放在一个工具对象中便于注册，但发送给模型时只转换出声明。</p><p>parameters 是运行时可用的 schema。TypeScript 的类型在运行时不会自动检查模型生成的 JSON，所以运行时仍要调用 validateToolArguments。类比 Go：把 JSON 解码到结构体，仍不能省略业务字段约束；“有静态类型”不是“输入已经可信”。</p><aside class="note"><strong>toolCall ID 的来源：</strong>更准确地说，它来自 provider 返回的工具调用协议，不必假定是神经网络自己生成。Anthropic 适配器直接采用响应中的 tool-use ID；OpenAI Responses 适配器组合 call ID 与 item ID；Google 响应缺少 ID 或发生重复时，Pi 会用工具名、时间和计数器补生成。无论来源如何，后续代码只把它作为不透明关联键。</aside>"""),
            ("pipeline", "执行管线的顺序为何重要", """<p>prepareToolCall 先找工具，按需要 prepareArguments，再校验参数，随后调用 beforeToolCall；只有允许执行的调用才进入 execute。执行完成后 afterToolCall 可覆写部分结果，最后形成工具事件和 toolResult。</p><p>顺序有明确含义：beforeToolCall 看到的是已校验参数；不存在的工具不会调用 execute；执行抛错会转为 isError 结果；被预检拦截的调用不经过正常执行后的覆写管线。afterToolCall 的 content 覆写是整个字段替换，不是自动深合并。</p><p>输出分为 content 与 details：前者用于模型可消费的内容，后者可以承载结构化展示或记录信息。不要把大量内部诊断直接塞进 content，否则它们也会成为后续推理的输入。</p>"""),
            ("parallel", "两种顺序：完成顺序和对话顺序", """<p>默认并行模式先按顺序预检全部调用，再并发执行允许的调用。假设 assistant 先提出 A 再提出 B，而 B 先完成：tool_execution_end 可先报告 B，让界面及时展示进度；随后工具结果消息仍按 A、B 的源顺序发布并进入对话。</p><p>这是 Promise.all 的一个重要性质：完成时间不固定，返回结果按输入顺序组织。它不是 CPU 多线程承诺，但可重叠异步 I/O。若批次中任一工具声明 sequential，整批采用串行路径，而非只把该工具单独锁住。</p><p>文件工具还有更细的互斥机制：相同文件的修改按规范化路径排队，不同文件仍可并行。队列是进程内机制，不是跨进程锁；测试覆盖符号链接别名和取消期间的锁持有。</p>"""),
            ("extensions", "扩展点让产品能力可组合", """<p>SDK 接受 customTools 与 resourceLoader，并将扩展 runner 接入上下文、请求头、请求体等钩子。仓库的 custom-compaction 示例通过 session_before_compact 提供摘要结果，说明上层可以替换策略而不重写基础循环。</p><p>这种可扩展性依赖生命周期契约：什么时候加载，回调拿到什么上下文，返回结果如何被解释，失败时谁负责处理。插件数量不是设计质量的指标；扩展是否绕过重要不变量，才是需要追问的问题。</p><p class="analysis">分析推断：钩子降低了定制门槛，也增加了执行顺序和故障传播的复杂度。类型能约束一部分输入输出，但不能保证第三方回调快速、可取消或没有副作用。</p>"""),
            ("permissions", "拦截钩子不等于沙箱", """<p>beforeToolCall 能阻止经过该管线的工具调用，却不自动限制整个进程的网络、文件和凭据访问。仓库根 README 明确说明，pi 默认以启动进程的权限运行，没有内置的通用权限限制系统。</p><p>因此，工具 schema 解决“参数形状”，钩子解决“调用策略”，隔离环境解决“实际权限”。三者不是互相替代的方案。本书不运行工具演示的真实副作用；交互区只展示教学状态转换。</p>"""),
        ],
        "evidence": [("packages/agent/src/agent-loop.ts", "function createToolResultMessage", 13, "工具结果复制调用请求的 ID，运行时不按工具名猜测配对。"), ("packages/ai/src/api/anthropic-messages.ts", "id: event.content_block.id", 9, "Anthropic 适配器采用 provider 响应中的 tool-use ID。"), ("packages/ai/src/api/openai-responses-shared.ts", 'if (item.type === "function_call")', 15, "OpenAI Responses 适配器组合调用 ID 与响应项 ID。"), ("packages/ai/src/api/google-generative-ai.ts", "Generate unique ID if not provided", 14, "Google 未提供 ID 或 ID 重复时，适配器补生成唯一值。"), ("packages/agent/src/agent-loop.ts", "const validatedArgs = validateToolArguments", 17, "校验发生在 beforeToolCall 之前。"), ("packages/agent/src/agent-loop.ts", "const orderedFinalizedCalls = await Promise.all", 12, "并发完成后，结果按源顺序发布。"), ("packages/agent/src/agent-loop.ts", "const hasSequentialToolCall", 8, "单个串行声明使整批走串行分支。"), ("packages/coding-agent/src/core/tools/file-mutation-queue.ts", "export async function withFileMutationQueue", 33, "同文件操作有进程内队列。"), ("README.md", "Pi does not include a built-in permission system", 1, "权限边界是项目明示的限制。")],
    },
    {
        "slug": "context", "title": "记住历史，不等于发送全部历史", "subtitle": "会话是记录，上下文是投影，运行状态是此刻。", "level": "核心", "diagram": "context",
        "intro": "长任务的难点并非把 messages 数组保存下来，而是决定下一次请求应看到哪些信息。pi 将持久记录与模型输入区分开，使会话可以保留历史，同时控制上下文规模。",
        "sections": [
            ("three", "三个容易混淆的对象", """<table><thead><tr><th>对象</th><th>回答的问题</th><th>例子</th></tr></thead><tbody><tr><td>会话记录</td><td>曾经发生过什么？</td><td>消息、模型变更、压缩记录、分支摘要</td></tr><tr><td>模型上下文</td><td>下一次请求交给模型什么？</td><td>规则、摘要、近期消息与工具结果</td></tr><tr><td>运行状态</td><td>现在正在做什么？</td><td>isStreaming、部分响应、pendingToolCalls</td></tr></tbody></table><p>例如 UI 正在显示的半句响应属于运行中的部分消息；一次压缩后，磁盘里仍可保留旧消息，但下一次模型请求只包含摘要和保留部分。将它们当成同一个数组，会使恢复、展示和预算管理互相牵制。</p>"""),
            ("storage", "session 文件保存的不是 AgentSession", """<p><strong>问题：</strong><code>AgentSession</code> 包含工具实现、事件监听器、取消控制器和正在执行的 Promise，不能可靠地直接序列化。Pi 因此不保存这个对象，而是让 <code>SessionManager</code> 保存足以恢复工作的记录。</p><p>默认路径是 <code>~/.pi/agent/sessions/--&lt;编码后的工作目录&gt;--/&lt;时间&gt;_&lt;session-id&gt;.jsonl</code>。JSONL 表示“一行一个 JSON 对象”：第一行是 header，记录版本、session ID、创建时间、cwd 和可选的父 session 文件；其余行是追加的 entry。</p><pre><code>{"type":"session","version":3,"id":"...","cwd":"/project"}\n{"type":"message","id":"a1","parentId":null,"message":{"role":"user","content":"..."}}\n{"type":"message","id":"b2","parentId":"a1","message":{"role":"assistant","content":[...]}}\n{"type":"model_change","id":"c3","parentId":"b2","provider":"...","modelId":"..."}</code></pre><p>Pi 当前保存 message、模型与 thinking level 变化、压缩摘要、分支摘要、标签、会话名称和扩展数据。assistant 消息中还可能包含 toolCall、usage 和终止原因；toolResult 保存调用 ID、输出与错误状态。每个 entry 的 <code>id + parentId</code> 形成树，文件最后追加的 entry 通常是恢复时的活动 leaf。</p><p>它不保存可执行的工具函数、监听器、网络连接、AbortController 或流式中的 <code>pending</code> assistant 消息。恢复过程是：读取 JSONL 并迁移旧版本 → 建立 ID 索引 → 从 leaf 沿 parentId 选出当前分支 → 应用最近的压缩记录 → 得到 messages、model 与 thinking level → 创建新的 Agent 和 AgentSession。新会话还会延迟到出现第一条完整 assistant 消息后才真正创建文件，避免只留下未完成的空会话。</p><aside class="note"><strong>与 Codex 对比（2026-09-20）：</strong>OpenAI 官方文档确认 Codex 将本地状态放在 <code>CODEX_HOME</code>（默认 <code>~/.codex</code>），session transcript 位于 <code>$CODEX_HOME/sessions</code>，归档位于 <code>archived_sessions</code>；可配置的本地历史还涉及 <code>history.jsonl</code>。本机当前实现可观察到按年月日组织的每 session JSONL，按顺序记录 <code>session_meta</code>、<code>turn_context</code>、<code>response_item</code>、<code>event_msg</code>、<code>compacted</code> 和 token usage 等事件。后者是实现观察，不是稳定公开格式。</aside><p>两者都选择追加事件而不是序列化整个运行对象，但关注点不同：Pi 的公开 session 格式用 <code>parentId</code> 直接表达对话分支；当前 Codex 记录更像带 ordinal 的执行轨迹，包含每 turn 的环境、权限、模型响应项和用量。实现自己的 harness 时，先保存可恢复的语义事件和外部副作用结果；不要从第一天复制某个产品的全部诊断字段。</p><p class="source-note">Codex 位置依据：OpenAI 官方文档《Troubleshooting》和《Advanced Configuration》（2026-09-20 核对）。Pi 格式依据本仓库 <code>session-manager.ts</code> 与 <code>docs/session-format.md</code>。</p>"""),
            ("tree", "会话树表达探索历史", """<p class="documented">项目文档：当前 coding-agent 会话以 JSONL 保存，条目通过 id 与 parentId 形成树，当前位置用 leaf 表达。JSONL 是逐行 JSON 的存储格式；树是条目之间的逻辑关系，两者并不冲突。</p><p>从一个早期问题尝试两条解决路线时，线性聊天必须复制或删除历史，树可以保留共同祖先并切换路径。模型上下文由所选路径构建，不会自动混合所有分支。离开分支时的摘要可以把有用进展带回新路径，但它不等于把两个程序状态自动合并。</p><p>这里也不是 Git 工作树：切换会话分支不意味着磁盘文件同步回到旧版本。对 C++/Rust 工程师，这是最值得防止的误解。</p>"""),
            ("compact", "压缩的基本步骤", """<p>shouldCompact 比较 contextTokens 与 contextWindow − reserveTokens，为后续生成保留空间。prepareCompaction 找到保留边界，收集需要摘要的旧消息；compact 生成结构化摘要；产品层保存压缩条目并重建上下文。</p><p>切点不能任意落在 toolResult 前面，否则模型会收到没有对应调用的结果。源码选择用户类消息或 assistant 消息作为有效切点；若在 assistant 工具调用前切开，它后面的结果一起保留。遇到一个特别长的用户轮次，还会单独摘要被切掉的轮次前缀。</p><p>前次摘要也参与后续压缩；文件操作信息会累计。这里的目标不是无损压缩，而是保留继续任务所需的目标、约束、进展和关键决定。摘要依然由模型生成，可能遗漏重要内容。</p>"""),
            ("failure", "预算与失败也属于摘要设计", """<p>estimateContextTokens 尽量使用最后一次有效 usage，再估算其后的消息；没有有效 usage 时估算全部消息。字符数除以四等规则是启发式，不是实际 tokenizer。特别对不同语言和多模态输入，不能把它当作精确计量保证。</p><p>摘要响应达到 length 时 getSummarizationFailure 会拒绝把不完整内容当作检查点；摘要如果试图调用工具，也会被拒绝。为什么如此保守？原始任务可以在工具错误后继续尝试，但错误摘要一旦成为后续上下文，会持续污染之后的推理。</p><p>源码将选切点、组织摘要输入、模型调用和存储职责分开。文件顶部虽称 pure functions，摘要函数实际上会调用模型；应按函数逐个判断副作用，不照单全收标题。</p>"""),
            ("cost", "用可恢复记录换取有限的模型视野", """<p class="analysis">分析推断：保留完整会话并为模型构建投影，使人类审计与模型预算不必使用同一种表示。代价是多了一套重建规则，摘要有成本和信息损失，压缩后的模型也无法“凭空回忆”未被保留的细节。</p><p>上下文工程在这里不是神秘技巧，而是信息选择与一致性工程：哪些数据保留、何时变换、调用和结果怎样保持配对、失败后从哪里恢复。先理解这四件事，再讨论更复杂的长期记忆或检索系统。</p>"""),
        ],
        "evidence": [("packages/coding-agent/src/core/session-manager.ts", "export interface SessionHeader", 18, "session 文件的 header 与条目类型，证明文件不是 AgentSession 对象快照。"), ("packages/coding-agent/src/core/session-manager.ts", "Manages conversation sessions as append-only trees", 16, "SessionManager 用追加日志和 parentId 树管理持久记录。"), ("packages/coding-agent/src/core/sdk.ts", "const existingSession = sessionManager.buildSessionContext();", 20, "恢复时先从记录构建上下文，再创建 Agent 与 AgentSession。"), ("packages/coding-agent/src/core/compaction/compaction.ts", "export function shouldCompact", 4, "压缩触发阈值。"), ("packages/coding-agent/src/core/compaction/compaction.ts", "function isCutPointMessage", 17, "不能在工具结果处单独切开。"), ("packages/coding-agent/src/core/compaction/compaction.ts", "export function getSummarizationFailure", 9, "输出达到上限时拒绝不完整摘要。"), ("packages/coding-agent/src/core/messages.ts", 'case "compactionSummary":', 10, "应用摘要转换成模型可消费消息。"), ("packages/coding-agent/docs/session-format.md", "Sessions are stored as JSONL", 8, "当前公开文档定义路径、版本和 JSONL 条目格式。")],
    },
    {
        "slug": "infrastructure", "title": "从本地助手走向可组合系统", "subtitle": "先问需要跨越什么边界，再决定引入什么基础设施。", "level": "进阶", "diagram": "infrastructure",
        "intro": "基础循环能处理一次运行，但多界面、进程断开和持久恢复带来另一组问题。本章区分当前 SDK 路径、新模块公开接口与实验性协议，不把仓库里的所有设计都宣称为稳定产品行为。",
        "sections": [
            ("lifecycle", "当前产品：资源跟随会话生命周期", """<p>AgentSessionRuntime 持有 session 及绑定工作目录的服务。切换项目时，它先取消并等待当前会话，再清理旧服务并构造新运行时；只替换 messages 会让旧工具闭包和目录设置泄漏到新项目。代价是新运行时创建失败时旧运行时已经拆除，因此调用者仍要处理非原子切换。</p>"""),
            ("chord", "Chord：需要多运行环境时再读", """<p class="documented">项目文档：Chord 用 facet、类型化服务和依赖顺序组合 worker 与展示端能力，并从权威端向消费端复制状态。它解决多环境装配和观察问题，不是基础 Agent 循环的必需层，也不是允许任意多端同时写入的 CRDT。</p>"""),
            ("protocol", "Protocol：跨进程才需要的路由层", """<p class="documented">实验模块文档：pi-protocol 负责请求关联、目标、取消和订阅帧；attachmentId 防止旧界面的延迟请求误投到新挂接。断连只说明本地不再等待，远端工作可能已经执行，因此默认不自动重放有副作用的请求。</p>"""),
            ("client-server", "Client 与 Server：远程访问 Session 的两端", """<p><strong>问题：</strong>当 UI 和 Agent Harness 不在同一个进程时，UI 不能直接拿到内存中的 Session 对象，也不能把任意网络连接都当作当前会话。Pi 的实验栈把连接、路由和业务服务分开。</p><table><thead><tr><th>包</th><th>负责什么</th><th>不负责什么</th></tr></thead><tbody><tr><td><code>pi-client</code></td><td>通过应用提供的有序字节传输连接服务端；校验 serverId；关联 request/response；发出取消；订阅 Chord service；保存当前 Session attachment 路由。</td><td>不执行 Agent，不保存权威 Session，不自动理解 transcript 或工具。</td></tr><tr><td><code>pi-protocol</code></td><td>定义 CBOR 帧、握手、请求/响应/取消/订阅信封，以及 serverId、sessionId、attachmentId 组成的目标地址。</td><td>不规定 Chord service 的业务参数，也不提供认证和自动重连策略。</td></tr><tr><td><code>pi-server</code></td><td>监听经过认证的字节连接；验证请求目标；管理每个展示连接的 attachment；把不透明的 service 调用转发给目标 Session endpoint；在关闭时释放句柄。</td><td>不是模型供应商服务，不自行实现 Agent 业务，也不决定 Session 如何持久化。</td></tr></tbody></table><p>一个具体轨迹是：远程界面创建 Client → 与指定 serverId 握手 → 通过服务端管理 service 请求 attach 某个 sessionId → Server 创建该展示端专属的 attachmentId 并异步通知 Client → 此后的 Session 请求必须携带完整三元组 → Server 校验仍是当前挂接后，才把 Chord service 调用转给 Session worker。</p><p>为什么除了 sessionId 还需要 attachmentId？同一个 Session 可以被多个展示端观察，一个连接也可能先后切换 Session。若旧请求在网络中延迟，只检查 sessionId 可能把它误投给新的挂接；server 生成的 attachmentId 把请求限定在“这一次活跃展示关系”中。</p><p>连接断开时，Client 会在本地拒绝 pending request，并清除 live attachment，但 Server 已经接收的工作仍可能完成。因此 Client 不自动重连和重放请求；调用方需要重新连接、重新 attach，并且只重试能证明安全的操作。这是远程副作用系统的核心难点，不是普通网络错误处理细节。</p><aside class="note"><strong>当前集成状态：</strong><code>coding-agent</code> 对 client、protocol、server 的导入集中在 <code>src/experimental/</code> 及实验测试；普通 CLI 主流程使用的是本地 AgentSessionRuntime。这里研究的是演进中的远程架构，不是当前每次 <code>pi</code> 请求的默认路径。</aside>"""),
            ("durable", "Durable：恢复的核心是未知副作用", """<p>当前公开入口主要是 MemoryStorage、记录类型与存储契约，不能把设计文档中的完整运行时当成当前默认路径。</p><p class="analysis">分析推断：如果文件已经写完而完成记录尚未落盘，恢复时既不能假定成功，也不能盲目重试。持久化 Harness 必须一起设计操作身份、幂等性和恢复策略；只有数据库并不等于 exactly-once。</p>"""),
            ("matrix", "模块地图与引入成本", """<table><thead><tr><th>模块组</th><th>解决的问题</th><th>学习重点 / 代价</th></tr></thead><tbody><tr><td>coding-agent / tui</td><td>用户如何操作和观察任务</td><td>生命周期、事件展示；界面状态不等于任务状态</td></tr><tr><td>agent / Harness / Session</td><td>执行与会话能力</td><td>基础循环之外，还有存储、恢复与上下文边界</td></tr><tr><td>chord</td><td>能力组合与状态复制</td><td>依赖图、激活和释放；额外间接层</td></tr><tr><td>protocol / client / server</td><td>跨进程路由与连接</td><td>挂接身份、断连与结果未知；实验性接口</td></tr><tr><td>durable / session-backends</td><td>不同层次的记录与存储实现</td><td>核对具体接口，不假定互相替换或已统一</td></tr><tr><td>telemetry / evals</td><td>运行观测与效果评估</td><td>观测不能代替状态；本书仅给模块定位，不深入实现</td></tr></tbody></table><p class="analysis">分析推断：这些复杂度在多进程、多界面与恢复需求出现后有价值。最值得学习的并非“项目应该有这么多包”，而是每增加一层都能说清它隔离了哪种变化。</p>"""),
        ],
        "evidence": [("packages/coding-agent/src/core/agent-session-runtime.ts", "private async teardownCurrent", 12, "切换时先等待当前运行，再释放上下文。"), ("packages/chord/README.md", "- **Plugins**", 13, "项目文档：服务声明与 facet 生命周期。"), ("packages/client/README.md", "On disconnect or disposal", 8, "Client 断连后不自动重放可能已有副作用的请求。"), ("packages/server/README.md", "A Session may have multiple presentation attachments", 10, "Server 用展示端 attachment 隔离多端和过期路由。"), ("packages/protocol/README.md", "All envelope schemas reject", 3, "实验协议的验证与认证边界。"), ("packages/durable/src/index.ts", "export { MemoryStorage }", 25, "目前实际公开的持久存储契约。")],
    },
    {
        "slug": "principles", "title": "把实现读成设计判断", "subtitle": "学习可解释的取舍，而不是收集架构口号。", "level": "综合", "diagram": "principles",
        "intro": "下面的原则是对已核对代码的分析归纳，不冒充作者的官方宣言。每一条都带具体问题、机制与代价；优秀与否必须放回 pi 的任务和边界里判断。",
        "sections": [
            ("contracts", "原则一：让变化在边界处收敛", """<p>问题：模型 API 和应用消息都在变化。例子：扩展加入一种 custom 消息，供应商又不接受中途 system 更新。方案：应用消息先由 convertToLlm 转换，再交给协议适配层处理服务差异。</p><p>收益是循环不用同时知道 UI 角色和每家 API 的格式；代价是多一层转换，错误也可能在转换中产生。必要性来自两个独立变化轴，而不是因为“层越多越高级”。一个只接单一 API 的固定流程未必需要同样规模的适配设施。</p><p>源码阅读入口：messages.ts 的角色转换、agent-loop.ts 的调用边界、ai/types.ts 的规范化上下文。</p>"""),
            ("state", "原则二：区分事实、视图和过程", """<p>问题：历史需要完整、模型输入需要有限、UI 又需要实时。方案：会话记录、上下文投影和运行状态分开，使用事件让展示跟进过程。</p><p>这个思想类似数据库中的记录与查询视图，但不要把所有 pi 模块都概括为完整的 event sourcing 系统。基础 Agent 仍在内存里维护可变状态，部分事件对象也不是不可变快照。</p><p>收益是压缩不必抹去审计历史；代价是恢复和投影规则必须一致。检查设计时应问：哪个对象是权威来源？哪些值能重建？发生失败时谁负责持久保存？</p>"""),
            ("ordering", "原则三：把时间顺序写成契约", """<p>问题：并发读取 B 比 A 先完成，UI 要尽快更新，对话却需要稳定顺序。方案：执行结束事件按完成时机发布，结果消息按调用源顺序发布。</p><p>同样，agent_end 与 idle 分开，取消与 I/O 结算分开。收益是接入者可以明确判断何时开始下一次工作；代价是事件名称本身不足以解释全部行为，必须阅读等待规则。</p><p>值得借鉴的是“区分几个看起来相同的完成时刻”。不应机械复制事件数量，也不应以回调很多来证明系统先进。</p>"""),
            ("effects", "原则四：副作用比纯数据更需要保守处理", """<p>问题：被截断的 JSON 可能还能解析，但缺少关键内容。方案：模型因 length 停止时不执行该响应中的工具调用。问题：取消后的文件写入可能仍在进行。方案：修改队列等实际操作结束后才释放。</p><p>这些判断都优先避免不完整输入或未知完成状态造成额外损坏。代价是某些本来可能有效的调用也会被拒绝，需要重新生成。对真实文件操作，这个保守选择通常比“尽量执行”更容易解释。</p><p>边界仍然存在：预检不是沙箱，进程内队列不是分布式锁。局部不变量成立，并不意味着整个执行环境已经安全。</p>"""),
            ("extension", "原则五：可扩展，但保持核心责任可见", """<p>问题：不同用户想换工具、摘要策略和界面。方案：通过函数注入、工具契约与生命周期钩子接入。SDK 是集中装配点，核心循环保留明确流程。</p><p>收益是定制通常不需要复制循环。代价是扩展行为会影响状态和时间顺序，宿主需要限制和解释回调的作用范围。当前默认 streamFn 又提示我们：现实代码会同时存在新接口与兼容路径，不能只提炼最理想的一面。</p><p>对代码风格的归纳是：普通函数与接口承载多数设计，联合类型表达分支，显式 await 表达顺序，短注释说明不变量与异常情形。并非每个文件都简单；AgentSession 的职责和体量也提示产品演进会累积复杂度。</p>"""),
            ("evaluate", "如何判断你已经理解这套设计", """<p>试着向同事解释：为什么模型不能自己读文件；为什么工具结果必须回到下一次请求；为什么同一条会话不等于每次发送同一批消息；为什么“取消成功”不能证明文件没有修改；为什么一个新的包不代表它已成为 CLI 的默认路径。</p><details class="reference-answer"><summary>查看参考答案</summary><ol><li><strong>为什么模型不能自己读文件？</strong> 模型只生成数据；文件读取是宿主拥有的副作用。通过工具边界，宿主才能验证参数、限制权限、记录行为并返回真实结果。</li><li><strong>为什么工具结果必须回到下一次请求？</strong> 工具在模型服务之外执行，模型不会自动知道结果。只有把 toolResult 加入上下文，下一 turn 才能依据外部事实继续推理。</li><li><strong>为什么同一条会话不等于每次发送同一批消息？</strong> session 是完整权威记录，模型请求是按当前分支、预算、压缩和过滤规则构建的投影；记录相同也可能产生不同请求视图。</li><li><strong>为什么“取消成功”不能证明文件没有修改？</strong> 取消是协作信号，不会回滚已经开始或提交的 I/O。必须等待具体工具结算或通过额外事务机制确认副作用状态。</li><li><strong>为什么一个新的包不代表它已成为 CLI 的默认路径？</strong> 包可能是实验接口、未来方向或独立能力。只有从产品入口追踪到实际调用，并核对公开导出和测试，才能判断当前集成状态。</li></ol></details><p>如果能用具体执行轨迹回答这些问题，你已经获得了迁移到 Go 或 Rust 的设计基础。下一步应根据自己的任务选择需要的边界，而不是把 pi 的目录结构整体翻译一遍。</p><p class="analysis">最终判断：pi 提供了值得研究的边界设计、显式生命周期和可扩展机制，也存在兼容状态、复杂回调与演进中接口。本书把它当作真实工程案例，不给出缺少比较基准的“行业第一”结论。</p>"""),
        ],
        "evidence": [("packages/agent/src/agent-loop.ts", "// A \"length\" stop", 10, "不完整响应中的工具调用不执行。"), ("packages/agent/src/agent.ts", "* `agent_end` is the final emitted", 3, "完成事件与空闲状态之间有明确边界。"), ("packages/coding-agent/src/core/sdk.ts", "setDefaultStreamFn(streamSimple)", 1, "兼容默认值仍真实存在。"), ("packages/coding-agent/src/core/messages.ts", "export function convertToLlm", 18, "应用角色转换集中在一个边界。")],
    },
]

# A compact decision lens shown before each chapter. These are design-analysis
# summaries, not claims made by pi's authors.
CHAPTER_GUIDES = {
    "foundations": {
        "priority": "必须掌握",
        "why": "Pi 同时存在产品会话、持久记录、执行状态和模型轮次。先区分这些对象，才能准确理解取消、压缩、恢复和工具执行发生在哪一层。",
        "industry": "多数 SDK 都区分 runner、run、turn、message、tool 与 session，但命名不统一。有的 Session 只指消息存储，有的还包含可恢复运行状态，因此必须回到具体代码确认边界。",
        "build": "先定义你的领域词汇和包含关系：谁长期存在、谁只在一次执行中存在、谁是权威记录、谁可以重建。再写循环。",
        "ignore": "先忽略多 Agent、长期记忆、插件市场和复杂 UI；也不要把其他框架的 Session 定义直接套到 Pi。",
    },
    "architecture": {
        "priority": "必须掌握",
        "why": "模型协议、执行循环和产品会以不同速度变化。若混在一个对象里，更换供应商、增加工具或恢复会话都会互相牵连。",
        "industry": "常见分层是 provider adapter、agent runner、tool runtime、session/product shell。图式框架会再加入节点和状态图；轻量 SDK 往往保留普通代码循环。",
        "build": "先做三个边界：模型适配、执行内核、产品装配。依赖从装配点注入；每层只拥有一种变化原因。",
        "ignore": "照搬 monorepo 包数量。Pi 的目录反映产品演进，不是创建新项目时必须复制的模板。",
    },
    "journey": {
        "priority": "必须掌握",
        "why": "一次用户请求可能包含多次模型调用。工具结果只有作为新消息回到模型，才会影响下一步判断。",
        "industry": "直接工具循环与多数 SDK 都采用 call → execute → append result → call again。图式工作流把同一过程显式表示成节点和边，便于固定分支与恢复。",
        "build": "先画清一次完整时序，给每个 tool call 稳定 ID，明确什么时候追加消息、什么时候结束、什么时候算运行真正结算。",
        "ignore": "流式界面的逐字效果。流式输出改善体验，却不决定 Agent 是否正确。先保证非流式完整路径成立。",
    },
    "control": {
        "priority": "必须掌握",
        "why": "模型可能持续调用工具，用户也可能中途介入。没有预算、取消和明确的完成边界，循环就可能失控或留下未知副作用。",
        "industry": "Runner 通常提供 max turns、取消信号、hooks 与事件；可恢复图运行时还会把中断点写入持久状态。Pi 侧重显式循环、队列和生命周期事件。",
        "build": "至少加入轮数或费用预算、超时、协作式取消和终止原因。把“发出结束事件”“监听器完成”“外部 I/O 完成”分开。",
        "ignore": "一开始就做跨进程调度。单进程中先证明状态机和副作用结算规则，再决定是否需要持久运行。",
    },
    "models": {
        "priority": "重要",
        "why": "不同模型 API 的消息、工具调用和流事件不同；但抹平全部差异又会丢失推理签名、缓存和续接能力。",
        "industry": "SDK 通常定义统一模型接口，再通过 provider adapter 保留供应商扩展字段。另一种做法是只支持单一 API，以更小的抽象换取更强耦合。",
        "build": "只抽象循环真正需要的最小契约：消息、工具声明、流事件、用量与停止原因。允许适配层携带不透明扩展数据。",
        "ignore": "项目初期同时兼容所有供应商。先支持一个真实模型，把适配边界留对；第二个 provider 出现后再验证抽象。",
    },
    "tools": {
        "priority": "必须掌握",
        "why": "工具把概率输出变成真实副作用，是 Agent 最危险也最有价值的边界。TypeScript 类型不能替代运行时参数校验。",
        "industry": "函数工具普遍采用 schema + handler；生产系统再增加 guardrail、权限、审批、隔离和审计。MCP 标准化连接方式，但不自动提供授权或沙箱。",
        "build": "区分声明、验证、策略、执行和结果。对写操作设计幂等键或明确的不可重试规则，并限制路径、网络和命令能力。",
        "ignore": "先做通用工具市场。少量边界清楚、描述准确、结果受控的工具，比几十个模糊工具更适合第一版 Harness。",
    },
    "context": {
        "priority": "必须掌握",
        "why": "完整历史会持续增长，而模型窗口有限。若把记录和请求混为一谈，压缩会破坏审计，或请求迟早超过预算。",
        "industry": "常见策略包括完整历史、滑动窗口、摘要、检索和服务端会话。成熟系统通常把权威记录与本次模型投影分开。",
        "build": "保存可审计记录，为每次请求构建投影；保证 tool call 与 result 成对。先做可测的截断与预算，再考虑检索和长期记忆。",
        "ignore": "向量数据库和“无限记忆”叙事。没有明确检索目标、质量评估和隐私边界时，它们只会增加不确定性。",
    },
    "infrastructure": {
        "priority": "按需了解",
        "why": "只有当任务跨进程、跨界面、跨重启或需要人工暂停时，内存中的循环才不够。Pi 仓库中的 Chord、protocol、client 和 Durable 面向这些边界。",
        "industry": "图运行时以 checkpoint 和 interrupt 支持恢复；工作流引擎把模型与工具调用包装成持久 activity；事件运行时适合松耦合组件。成本都是更多状态和失败模式。",
        "build": "出现真实需求后再选：多界面需要状态复制，长任务需要 checkpoint，未知副作用需要操作身份与恢复策略。逐项引入。",
        "ignore": "第一版 Agent 可忽略 Chord、跨进程协议、分布式恢复和多后端存储。先理解它们解决的问题，不必读完实现。",
    },
    "principles": {
        "priority": "用于复盘",
        "why": "源码细节会变化，能够迁移的是边界判断：变化在哪里收敛、谁拥有副作用、何时真正完成、失败后如何恢复。",
        "industry": "框架在 API 形态上差异很大，但可靠系统都会处理工具契约、运行预算、可观测性、上下文投影和副作用恢复。差别在默认值与复杂度出现的时机。",
        "build": "用一张决策清单审查设计：输入是否可信、状态是否有权威来源、完成是否可判定、副作用是否可恢复、复杂度是否由需求驱动。",
        "ignore": "架构口号和框架排名。先用你的任务、失败成本和部署环境判断取舍，再选择库或自行实现。",
    },
}

# Visible self-check questions with answers rendered in a closed native details
# element. Foundations has a hand-authored check in its final section; the
# principles chapter embeds answers beside its existing synthesis questions.
CHAPTER_CHECKS = {
    "architecture": [
        ("执行 pi 命令后，TypeScript 入口和真正的 CLI 主函数分别在哪里？", "package.json 的 bin.pi 指向构建后的 dist/bundle/cli.js；对应源码入口是 packages/coding-agent/src/cli.ts。它调用 packages/coding-agent/src/main.ts 导出的 async main()，后者负责参数解析、运行时装配和模式分派。"),
        ("packages 下哪些目录属于理解当前 Pi CLI 的第一遍主线？", "先读 coding-agent、agent、ai，再按需看 tui。coding-agent 是产品与装配层，agent 是执行内核，ai 是模型适配，tui 是终端显示。Chord、protocol、client、server、durable、session-backends、telemetry 和 evals 都解决进阶或工程化问题，不应混入第一遍核心调用链。"),
        ("最小复刻 Pi 时，为什么说重点是 agent 和 ai，却仍需一个宿主层？", "ai 只提供模型协议，agent 只提供执行循环和状态；二者不知道你的入口、system prompt、具体工具、凭据来源和输出方式。宿主层负责装配这些策略。它可以很薄，因此无需复制完整 coding-agent，但不能完全不存在。"),
        ("为什么 agent 可以概念化为 agent-core，而 ai 不宜直接改称 provider？", "agent 的核心职责确实是持有状态并推进 Agent 执行；agent-core 或 agent-runtime 能表达这一点。ai 除具体 provider 外还定义统一 Model、消息、流、认证和用量，因此顶层更适合 model-runtime/model-api，provider 只适合作为其中的适配子层。"),
        ("什么时候一个模块更适合称为 harness，而不是 agent-core？", "只负责 run/turn 状态机、模型调用和工具循环时更像 agent-core/runner；当模块还统一管理工具资源、system prompt、上下文预算、Session、持久化恢复、权限和观测时，它才形成较完整的 harness。"),
        ("createAgentSession() 为什么是装配点，而不是 Agent 执行内核？", "它负责选择工作目录、设置、模型运行时、资源加载器和 SessionManager，再构造 Agent 与 AgentSession；真正的模型与工具循环位于 Agent/agent-loop，产品策略位于 AgentSession。"),
        ("这段 SDK Quick Start 已经在使用 Pi 吗？它还缺少什么？", "是。它已经创建 AgentSession 并通过 prompt 启动完整 Agent run。要真正得到模型响应，环境中还需有可用模型及凭据；要显示流式文本需订阅事件，或在完成后读取 messages。inMemory 会话不写磁盘，且这段代码没有 CLI 界面。"),
        ("pi-ai、pi-agent-core、pi-coding-agent 和 pi-tui 分别隔离什么变化？", "pi-ai 隔离模型协议；pi-agent-core 持有执行循环、工具和队列；pi-coding-agent 组织会话、具体工具、扩展和产品策略；pi-tui 负责终端展示与输入。"),
        ("为什么 StreamFn 作为函数注入，而不是让循环直接调用某家 SDK？", "循环只依赖“获得一次模型响应”的契约，因此测试可以注入假流，产品层可以替换 provider、超时和重试策略，而无需改动循环。代价是调用者必须遵守流的结算协议。"),
        ("为什么仓库里出现 Chord 或 Durable，不能证明当前 CLI 已以它们为主路径？", "包存在、公开导出和设计文档只证明能力或方向。判断当前路径必须从实际入口追踪调用关系，并区分稳定实现、实验模块和设计目标。"),
    ],
    "journey": [
        ("字符串输入到达模型前经历哪些主要边界？", "字符串先包装成 user AgentMessage；循环声明工具变化；transformContext 在应用消息层调整上下文；convertToLlm 转成模型消息；normalizeContext 形成标准请求，最后由 StreamFn 调用 provider。"),
        ("为什么 Pi 不在流式 toolCall 参数刚出现时立刻执行工具？", "增量参数可能尚未完成，也可能因长度限制而被截断。Pi 等完整 assistant message 和 stopReason 结算后再提取、校验和执行调用。"),
        ("为什么工具执行完成后通常还要再次请求模型？", "工具在宿主进程执行，模型不会自动看到结果。运行时必须把 toolResult 追加为消息，再发起下一 turn，模型才能基于真实结果继续判断。"),
        ("什么时候一次请求才算真正结算？", "循环确认没有工具续轮、steering 或 follow-up 后发送 agent_end；Agent 还会等待异步事件监听器完成，随后 finishRun 清除 active run，waitForIdle 才完成。"),
    ],
    "control": [
        ("steering、follow-up 和 abort 分别表达什么控制意图？", "steering 在当前 turn 结束后改变下一 turn；follow-up 在当前工作原本要结束时追加工作；abort 发出协作式取消信号，要求模型、工具和钩子停止正在进行的工作。"),
        ("follow-up 与等待结束后启动新 run 的边界差别是什么？", "follow-up 继续当前 active run，不先发送 agent_end，并沿用取消信号和运行边界；新 run 要等旧 run 完全结算，再创建新的 active run 并发送新的 agent_start。两者最终给模型的消息可能等价。"),
        ("为什么 abort 返回或信号触发后，不能断言文件没有变化？", "AbortSignal 是协作通知，不是事务回滚。底层 I/O 可能已经提交或仍在完成；只有具体操作的结算结果才能说明副作用状态。"),
        ("为什么同样叫事件，Agent listener 和低层 EventStream 的等待语义不同？", "Agent.processEvents 按序 await listener，因此监听器属于运行结算边界；EventStream.push 只把事件交给队列，不等待异步迭代消费者处理完成。"),
        ("工具失败与模型失败为什么采用不同默认处理？", "工具错误可以变成 isError toolResult 返回模型，让模型调整方案；模型 error/aborted 意味着没有可靠 assistant 响应，循环停止推进。"),
    ],
    "models": [
        ("provider 与 api 为什么不是同一个概念？", "provider 是服务来源，api 是线路协议；一个 provider 可以使用兼容其他厂商的 API。只按 provider 名称分支会把部署来源和消息协议混在一起。"),
        ("为什么既需要 convertToLlm，又需要 provider 适配？", "convertToLlm 处理应用消息角色和本地语义，provider 适配处理线路格式与服务差异。两个变化轴分开后，扩展消息不会泄漏进协议层，供应商差异也不会散落到产品代码。"),
        ("统一消息后，为什么仍保留 responseId、thinkingSignature 等字段？", "这些是不透明但必要的 provider 连续性数据。若为了表面统一而删除，后续 turn 可能失去推理续接、缓存或响应关联能力。"),
        ("一个可靠 StreamFn 最少要让上层得到什么？", "它要提供可消费的增量事件，并最终结算成包含内容、usage、stopReason 和错误信息的完整 AssistantMessage；桥接层还要处理某些底层 API 可能同步抛错的差异。"),
    ],
    "tools": [
        ("为什么 TypeScript 已有参数类型，运行时仍必须校验 schema？", "TypeScript 类型在运行时被擦除，而工具参数来自外部模型生成的 JSON。运行时 schema 才能检查字段、类型和约束。"),
        ("一次工具调用从模型数据到真实副作用的关键顺序是什么？", "查找工具 → 准备参数 → schema 校验 → beforeToolCall 策略 → execute → afterToolCall → 形成 toolResult。未知工具、非法参数和执行异常都应结算成明确结果。"),
        ("toolCall ID 从哪里来，为什么不能按工具名配对？", "ID 通常来自 provider 响应，缺失或重复时适配层可补生成；工具执行器把它复制到 toolResult。一次响应可以多次调用同名工具，所以名称不能唯一关联请求和结果。"),
        ("并行工具执行中，完成顺序与写入对话的顺序为何分开？", "完成事件按实际结束时间发布，便于 UI 及时更新；toolResult 消息仍按 assistant 中的调用顺序写入，给模型稳定、可复现的 transcript。"),
        ("beforeToolCall 为什么不能替代沙箱？", "钩子只能拦截经过该管线的调用，不能限制进程本身的文件、网络、子进程和凭据权限。参数校验、策略审批与系统隔离是三个不同层次。"),
    ],
    "context": [
        ("会话记录、模型上下文和运行状态分别是什么？", "会话记录是可审计的历史事实；模型上下文是本次请求从记录构建的有限投影；运行状态是此刻的流式消息、pendingToolCalls 和取消状态。"),
        ("Pi 为什么保存 session JSONL，而不是序列化 AgentSession？", "AgentSession 含函数、监听器、连接和取消控制器，不能作为稳定数据保存。JSONL 只记录可恢复事实，重启后由 SessionManager 构建上下文，再创建新的 Agent 与 AgentSession。"),
        ("JSONL 是线性文件，为什么仍能表示会话树？", "物理上每行顺序追加；逻辑上每个 entry 用 id 和 parentId 指向父节点。leaf 选择当前路径，分支只需从旧节点追加新的子节点。"),
        ("压缩后，旧消息是否从 session 中消失？", "不会。压缩追加 summary 与保留边界，模型上下文改用摘要和近期消息；完整 session 记录仍可保留旧条目用于审计和其他分支。"),
        ("为什么压缩切点不能让 toolResult 与 toolCall 分离？", "模型协议要求结果能关联先前调用。单独保留 toolResult 会产生孤儿结果并破坏上下文一致性，因此切点必须保持调用与结果的有效组合。"),
    ],
    "infrastructure": [
        ("什么时候内存中的 Agent 循环已经不够？", "当任务需要跨进程、跨界面、跨重启、长时间暂停或在断连后恢复时，才需要协议、状态复制、checkpoint 和持久运行设施。"),
        ("切换项目时为什么 AgentSessionRuntime 要重建服务，而不只替换 messages？", "工具和扩展闭包绑定 cwd、设置与资源。只换消息会让旧目录相关服务泄漏到新会话，因此必须取消旧运行、释放服务并按目标 cwd 重新装配。"),
        ("实验远程栈中的 client、protocol 和 server 分别负责什么？", "client 管理连接、请求关联、订阅和当前 attachment；protocol 定义 CBOR 帧及路由信封；server 验证目标并把不透明的 Chord service 调用路由到 Session endpoint。三者都不应该自行解释 Agent 的模型和工具业务。"),
        ("已有 sessionId，为什么远程请求还需要 attachmentId？", "sessionId 标识长期 Session，attachmentId 标识某个展示连接当前这一次挂接。连接切换或多端同时观察时，它能拒绝来自旧挂接的延迟请求，避免误投到新的活跃关系。"),
        ("连接断开为什么不能直接重试有副作用的请求？", "断连只证明调用方没有收到结果，远端操作可能已经执行。盲目重试可能重复写文件或执行命令，需要调用身份、状态查询或幂等策略。"),
        ("为什么有数据库仍不能自动获得 exactly-once？", "外部副作用和完成记录之间存在崩溃窗口：文件可能已写入，但数据库尚未记录成功。恢复必须处理未知结果，而不是仅依赖存储存在。"),
        ("如何判断 Chord、protocol 或 Durable 是当前实现还是演进方向？", "检查当前入口的真实调用链、公开导出、测试与文档成熟度。实验 README 和设计目标要单独标注，不能等同于默认 CLI 已使用。"),
    ],
}

GLOSSARY = [
    ("Agent", "模型与工具执行构成的反馈系统；在本书中以 pi 的具体运行时为准。", "foundations"),
    ("AgentSession", "coding-agent 的应用协调层，连接 Agent、持久会话、设置、扩展、压缩和重试，并向不同界面提供统一操作。", "foundations"),
    ("SessionManager", "当前 coding-agent 的持久会话管理器，保存带父子关系的消息和状态条目。", "foundations"),
    ("Harness", "围绕模型执行的宿主设施，管理工具、上下文与生命周期；新 Harness 的范围比基础循环更广。", "infrastructure"),
    ("Provider / API", "服务来源 / 协议实现。二者不是同一个维度。", "models"),
    ("Transcript", "按顺序组织的消息记录；其中的 system 更新也承载规则和工具变化。", "models"),
    ("Context", "当前操作的上下文；模型上下文与 Chord 的取消/调用上下文是不同概念。", "context"),
    ("Tool call / Tool result", "模型提出的结构化请求 / 程序执行后返回的反馈，通过调用 ID 关联。", "tools"),
    ("Token / Context window", "模型输入输出的计量单位 / 请求可以容纳的上下文容量。", "foundations"),
    ("Turn / Run", "低层 turn 是一次模型响应及其工具批次；一次 run 可有多个 turn。压缩模块的轮次定义不同。", "control"),
    ("Steering / Follow-up", "下一轮介入当前工作 / 当前工作本来要结束时追加任务。", "control"),
    ("Compaction", "用摘要与近期消息构建更小的模型上下文，不等于删除完整会话。", "context"),
    ("Promise / AsyncIterable", "未来完成的结果 / 可按到达顺序异步迭代的数据源。", "foundations"),
    ("Schema", "运行时可以验证的数据结构规则，与擦除后的 TypeScript 类型有别。", "tools"),
    ("Facet", "插件在某个运行环境中的组成部分，由宿主装配依赖与生命周期。", "infrastructure"),
    ("Attachment", "某个展示端与会话的一次挂接身份，用于拒绝过期路由。", "infrastructure"),
    ("Projection", "从记录中构建用于特定目的的视图，例如当前路径的模型上下文。", "context"),
    ("Side effect", "改变外部世界的操作，例如写文件；取消或重试需要考虑其真实完成状态。", "principles"),
]

DIAGRAMS = {
    "concept": ("Pi 核心对象与时间边界", "启动 Pi 后，运行时持有一个当前 AgentSession；该 Session 连接一个 Agent 与一个 SessionManager。一次普通消息启动 run，run 包含一个或多个 turn。", """flowchart TD
P[启动 Pi CLI] --> RT[AgentSessionRuntime 当前槽位]
RT -->|当前 1 个，可替换| AS[AgentSession 应用协调层]
AS -->|持有 1 个| A[Agent 执行内核]
AS -->|持有 1 个| SM[SessionManager 持久会话树]
A --> ST[AgentState 模型、工具与消息]
U[空闲时发送 user message] -->|prompt| R[一次 Run]
A --> R
R --> T1[Turn 1：assistant 响应]
T1 --> C[toolCall]
C --> AT[AgentTool.execute]
AT --> TR[toolResult]
TR --> T2[Turn 2：assistant 响应]
T2 --> E[Run 结算并回到空闲]
R -.产生的消息与状态变化.-> SM
"""),
    "architecture": ("CLI 与 SDK 主路径", "CLI 从 cli.ts 进入 main.ts 并选择运行模式；SDK 可直接从 createAgentSession 开始。两条路径最终使用相同的 AgentSession 与执行内核。", """flowchart TD
BIN[pi 命令] --> CLI[cli.ts]
CLI --> MAIN[main.ts main]
MAIN --> MODE{运行模式}
MODE -->|interactive| IM[InteractiveMode]
MODE -->|print| PM[runPrintMode]
MODE -->|rpc| RM[runRpcMode]
MAIN --> RT[AgentSessionRuntime]
RT --> ASSEMBLE[会话装配]
USER[SDK 用户] --> SDK[createAgentSession]
SDK --> ASSEMBLE
ASSEMBLE --> S[AgentSession]
ASSEMBLE --> A[Agent]
S --> A
S --> H[会话与扩展]
A --> L[agent loop]
L --> F[streamFn]
F --> M[ModelRuntime 与 pi-ai]
L --> T[工具执行]
A --> E[生命周期事件]
E --> UI[CLI 与其他消费者]
"""),
    "journey": ("一次请求的时序", "一次用户请求包含两次模型调用，中间经过一次 read 工具执行。", """sequenceDiagram
participant U as 用户
participant A as Agent
participant M as 模型
participant T as 工具
U->>A: 解释 README
A->>M: 消息与工具声明
M-->>A: read 调用
A->>T: 校验后执行
T-->>A: 文件内容
A->>M: 追加工具结果的消息
M-->>A: 最终解释
A-->>U: 完成
"""),
    "control": ("继续与结束的判定", "模型错误或取消终止；工具反馈与 steering 进入下一轮；follow-up 在原本会停止时消费。", """flowchart TD
Q[准备消息] --> M[请求模型]
M --> E{错误或取消}
E -->|是| X[结束]
E -->|否| T[处理工具批次]
T --> S{停止钩子}
S -->|停止| X
S -->|继续| N{工具续轮或 steering}
N -->|有| Q
N -->|无| F{follow-up}
F -->|有| Q
F -->|无| X
"""),
    "models": ("从应用数据到模型协议", "应用消息变换、模型消息转换、规范化与供应商适配是不同边界。", """flowchart TD
A[AgentMessage] --> B[transformContext]
B --> C[convertToLlm]
C --> D[normalizeContext]
D --> E[streamFn]
E --> F[API 适配]
F --> G[统一响应事件]
"""),
    "tools": ("工具调用的执行管线", "参数验证与策略拦截在实际副作用之前；失败也产生关联的工具结果。", """flowchart TD
A[工具调用] --> B[查找与参数准备]
B --> C[参数校验]
C --> D{beforeToolCall}
D -->|允许| E[execute]
D -->|拦截| X[错误结果]
B -->|未知工具| X
C -->|非法参数| X
E --> F[afterToolCall]
F --> G[结果结算]
X --> G
G --> H[下一轮模型上下文]
"""),
    "context": ("压缩改变模型视野，不删除历史", "会话记录保留完整路径；压缩前发送较长历史，压缩后发送摘要与近期消息，工具调用和结果仍保持配对。", """flowchart LR
H[完整会话记录] --> P1[压缩前投影]
P1 --> O[旧消息]
P1 --> R1[近期调用与结果]
H --> C[选择安全切点]
C --> S[生成并保存摘要]
S --> P2[压缩后投影]
P2 --> G[规则与摘要]
P2 --> R2[近期调用与结果]
H -.原始条目仍保留.-> S
"""),
    "infrastructure": ("实验服务边界", "展示端通过 client/protocol 路由服务调用，Chord 处理服务语义，应用拥有会话和工作进程。图不代表当前 SDK 的默认调用路径。", """flowchart TD
P[展示端] --> C[pi-client]
C --> R[pi-protocol 路由]
R --> S[pi-server]
S --> A[应用拥有的服务端点]
A --> F[Chord 服务语义]
F --> W[worker 内 Session 与 Harness]
W --> D[存储实现]
"""),
    "principles": ("用边界检查设计", "四个问题分别对应输入规范化、副作用校验、完成边界和恢复策略。", """flowchart TD
A[一个设计决策] --> B[输入是否可信]
A --> C[谁拥有副作用]
A --> D[何时真正完成]
A --> E[失败如何恢复]
B --> F[明确契约与代价]
C --> F
D --> F
E --> F
"""),
}
