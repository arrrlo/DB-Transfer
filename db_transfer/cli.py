import click

from db_transfer import Transfer


@click.group()
def cli():
    pass


@cli.command()
@click.option('-h', '--host', default='localhost', help='Redis host')
@click.option('-p', '--port', default=6379, help='Redis port')
@click.option('-d', '--db', default=0, help='Redis database')
@click.option('-p', '--prefix', default='prefix', help='Redis keys prefix')
@click.option('-n', '--namespace', default='namespace', help='Redis keys namespace')
def redis(host, port, db, prefix, namespace):

    class RedisHandler(Transfer):

        def __init__(self, prefix, namespace, host, port, db):
            super().__init__(prefix=str(prefix), namespace=namespace, adapter_name='redis')

            self.set_env('HOST', host)
            self.set_env('PORT', port)
            self.set_env('DB', db)

    rh = RedisHandler(prefix=prefix, namespace=namespace, host=host, port=port, db=db)

    try:
        from ptpython.repl import embed, run_config
        loc = {
            'rh': rh
        }
        embed(globals(), loc, history_filename='.data-handler_cli_history',
              configure=run_config)
    except ImportError:
        click.echo(click.style('Install ptpython for a better shell. \
            (pip install ptpython)', fg='red'))
        import code
        code.interact()
