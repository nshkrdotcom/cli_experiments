import click

def hello_world():
    """
    A simple command that prints 'Hello, World!'.
    """
    try:
        click.echo("Hello, World!")
    except Exception as e:
        click.echo(f"An error occurred: {e}")

if __name__ == '__main__':
    hello_world()