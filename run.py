venv_file = './venv/Scripts/activate_this.py'
exec(open(venv_file).read(), {'__file__': venv_file})

if __name__ == '__main__':
    from kirabot import bot
    import asyncio

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    bot.run(loop=loop)
