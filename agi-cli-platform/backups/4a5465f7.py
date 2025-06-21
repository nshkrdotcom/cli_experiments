import click

def greet_user(name):
    """
    Greets the user by name.

    Args:
        name (str): The name of the user to greet.

    Returns:
        str: A greeting message.
    """
    if not isinstance(name, str):
        raise TypeError("Name must be a string.")

    if not name:
        raise ValueError("Name cannot be empty.")

    greeting = f"Hello, {name}!"
    return greeting

@click.command()
@click.argument('name')
def greet(name):
    """Greets the user by name."""
    try:
        message = greet_user(name)
        click.echo(message)
    except (TypeError, ValueError) as e:
        click.echo(f"Error: {e}")

if __name__ == '__main__':
    greet()