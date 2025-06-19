import asyncio
from claude_code_sdk_fixed import query, ClaudeCodeOptions

async def quick_test():
    options = ClaudeCodeOptions(max_turns=2, allowed_tools=["Write"], permission_mode="bypassPermissions", cwd='.')
    msg_count = 0
    cost = 0
    async for msg in query(prompt='Write "SDK works!" to test.txt', options=options):
        msg_count += 1
        if hasattr(msg, 'total_cost_usd'):
            cost = msg.total_cost_usd
    return msg_count > 0 and cost > 0

success = asyncio.run(quick_test())
print(f'Messages: {msg_count}')
print(f'Cost tracked: ${cost:.4f}') 
print(f'SDK functional: {success}')