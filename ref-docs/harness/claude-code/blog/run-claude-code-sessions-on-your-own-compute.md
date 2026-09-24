Self-hosted environments for Claude Code | Claude by Anthropic
Explore here
Run Claude Code sessions on your own compute
Category
Product announcements
Product
Claude Code
Date
August 6, 2026
Reading time
5
min
Share
Copy link
https://claude.com/blog/run-claude-code-sessions-on-your-own-compute
Now in public beta, self-hosted environments let you run Claude Code sessions on your own infrastructure. Start a session from the web, mobile, desktop, or a routine, and it runs inside your network, next to your internal services, toolchains, and security controls, rather than on Anthropic-hosted infrastructure.
For most enterprises, we strongly recommend our hosted offering for operational simplicity with no infrastructure to run or maintain. Self-hosted environments are for teams whose network, tooling, or compliance requirements call for keeping agent execution on infrastructure they control. If you go this route, plan to staff engineering to own setup and ongoing maintenance.
Why self-host
We saw organizations in our preview program adopt self-hosted environments for a few key reasons:
Network access: sessions run inside your network and can reach internal services, databases, and registries without exposing them to the public internet
Customizability: pre-install compilers, SDKs, and internal CLIs in your environment so every session starts ready to build
Compliance: source code and build artifacts stay on infrastructure you control
“Self-hosted environments let us integrate Claude Code into our existing development workflows while maintaining our security and operational controls. This setup means Claude can generate PRs, help fix CI issues, and respond to developer workflow events, with compute that can scale based on demand. Claude understands our codebase, making it a strong fit for how our engineering teams build.”
George Jacob, Senior Engineering Manager
PrevPrev
0/5
NextNext
eBook
Data stays on your infrastructure
Repository checkouts, build artifacts, secrets, and any files a session creates or modifies all stay on infrastructure you provision.
The conversation itself, including prompts, responses, and tool results (which can include code that Claude reads), is sent to Anthropic for inference, and the session transcript is stored so a session can be picked up from any surface.
How it works
When using self-hosted environments, you deploy a set of runners. These long-lived processes pick up sessions and start a Claude Code process for each session. Runners come in two modes.
Fixed: you keep a set number running and sessions are distributed across them.
On-demand: an orchestrator watches for queued sessions, starts a runner as sessions arrive, and stops them when work finishes so capacity tracks demand.
Runners can serve more than one session, but each session runs in its own checkout, so work stays isolated between developers and accounts. Sessions from every supported surface route to the same environment, so you set it up once and it works wherever your team starts a session.
Note: Self-hosted environments differ from Remote Control, which lets developers continue sessions running on their own machines from a phone or browser. Sessions using Remote Control end when that machine stops running the session and are tied to the user who ran claude, whereas self-hosted environments run sessions on shared infrastructure your platform team operates and can be used by any user.
Getting started
Self-hosted environments are available in public beta to organizations on Claude Team and Enterprise plans. They are off by default and not available for organizations using ZDR.
Plan on a platform, developer experience, or developer productivity team owning setup and ongoing operation, including building and maintaining the runner image, updating runners, and running the orchestrator if you use on-demand mode.
See the documentation to learn more. Share feedback via GitHub or through your Anthropic account team.
FAQ
No items found.
Related posts
Explore more product news and best practices for teams building with Claude.
Oct 20, 2025
Claude Code on the web
Product announcements
Claude Code on the webClaude Code on the web
Claude Code on the webClaude Code on the web
Sep 16, 2026
Claude Cowork and chat are now one Claude
Product announcements
Claude Cowork and chat are now one ClaudeClaude Cowork and chat are now one Claude
Claude Cowork and chat are now one ClaudeClaude Cowork and chat are now one Claude
Sep 23, 2026
Claude Marketplace: one place to discover plugins, agents, and services from our partners
Product announcements
Claude Marketplace: one place to discover plugins, agents, and services from our partnersClaude Marketplace: one place to discover plugins, agents, and services from our partners
Claude Marketplace: one place to discover plugins, agents, and services from our partnersClaude Marketplace: one place to discover plugins, agents, and services from our partners
Sep 17, 2026
Projects redesigned: from folder to conversation
Product announcements
Projects redesigned: from folder to conversationProjects redesigned: from folder to conversation
Projects redesigned: from folder to conversationProjects redesigned: from folder to conversation
Transform how your organization operates with Claude
See pricing
See pricingSee pricing
Contact sales
Contact salesContact sales
Get the developer newsletter
Product updates, how-tos, community spotlights, and more. Delivered monthly to your inbox.
Thank you! You’re subscribed.
Sorry, there was a problem with your submission, please try again later.
Claude Code
