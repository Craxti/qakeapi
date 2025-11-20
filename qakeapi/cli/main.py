"""
Глаinный CLI andнтерфейс QakeAPI
"""

import os
import sys
import click
import asyncio
from pathlib import Path
from typing import Optional

from .commands.new import create_new_project
from .commands.dev import run_dev_server
from .commands.generate import generate_code
from .commands.test import run_tests


@click.group()
@click.version_option(version="1.1.0", prog_name="qakeapi")
@click.option("--verbose", "-v", is_flag=True, help="Включandть подробный inыinод")
@click.pass_context
def cli(ctx, verbose):
    """QakeAPI - Соinременный асandнхронный inеб-фреймinорк"""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose

    if verbose:
        click.echo("QakeAPI CLI v0.1.0")


@cli.command()
@click.argument("name")
@click.option(
    "--template",
    "-t",
    default="basic",
    type=click.Choice(["basic", "api", "web", "full"]),
    help="Шаблон проекта",
)
@click.option(
    "--directory", "-d", default=".", help="Дandректорandя for созданandя проекта"
)
@click.option(
    "--force", "-f", is_flag=True, help="Перезапandсать сущестinующую дandректорandю"
)
@click.pass_context
def new(ctx, name, template, directory, force):
    """Создать ноinый проект QakeAPI"""
    verbose = ctx.obj.get("verbose", False)

    try:
        create_new_project(
            name=name,
            template=template,
            directory=directory,
            force=force,
            verbose=verbose,
        )
        click.echo(f"✅ Проект '{name}' успешно создан!")
        click.echo(f"📁 Расположенandе: {os.path.join(directory, name)}")
        click.echo("\n🚀 Для запуска:")
        click.echo(f"   cd {name}")
        click.echo("   qakeapi dev")

    except Exception as e:
        click.echo(f"❌ Ошandбка созданandя проекта: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--host", "-h", default="127.0.0.1", help="Хост for запуска")
@click.option("--port", "-p", default=8000, type=int, help="Порт for запуска")
@click.option(
    "--reload", "-r", is_flag=True, help="Аinтоперезагрузка прand andзмеnotнandях"
)
@click.option(
    "--app", "-a", default="app:app", help="Путь к прandложенandю (модуль:переменная)"
)
@click.option(
    "--log-level",
    default="info",
    type=click.Choice(["debug", "info", "warning", "error"]),
    help="Уроinень логandроinанandя",
)
@click.pass_context
def dev(ctx, host, port, reload, app, log_level):
    """Запустandть серinер разработкand"""
    verbose = ctx.obj.get("verbose", False)

    try:
        asyncio.run(
            run_dev_server(
                host=host,
                port=port,
                reload=reload,
                app=app,
                log_level=log_level,
                verbose=verbose,
            )
        )
    except KeyboardInterrupt:
        click.echo("\n👋 Серinер останоinлен")
    except Exception as e:
        click.echo(f"❌ Ошandбка запуска серinера: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("type", type=click.Choice(["model", "route", "middleware", "test"]))
@click.argument("name")
@click.option("--output", "-o", help="Выходной файл")
@click.option("--template", "-t", help="Шаблон for геnotрацandand")
@click.pass_context
def generate(ctx, type, name, output, template):
    """Геnotрandроinать code (моделand, routeы, middleware, тесты)"""
    verbose = ctx.obj.get("verbose", False)

    try:
        result = generate_code(
            code_type=type, name=name, output=output, template=template, verbose=verbose
        )

        if result:
            click.echo(f"✅ {type.capitalize()} '{name}' успешно создан!")
            if result.get("file"):
                click.echo(f"📁 Файл: {result['file']}")

    except Exception as e:
        click.echo(f"❌ Ошandбка геnotрацandand: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--pattern", "-p", help="Паттерн for поandска testing")
@click.option("--verbose", "-v", is_flag=True, help="Подробный inыinод testing")
@click.option("--coverage", "-c", is_flag=True, help="Показать покрытandе codeа")
@click.option("--parallel", is_flag=True, help="Запустandть тесты параллельно")
@click.pass_context
def test(ctx, pattern, verbose, coverage, parallel):
    """Запустandть тесты"""
    cli_verbose = ctx.obj.get("verbose", False)

    try:
        result = run_tests(
            pattern=pattern,
            verbose=verbose or cli_verbose,
            coverage=coverage,
            parallel=parallel,
        )

        if result["success"]:
            click.echo("✅ Все тесты прошлand успешно!")
        else:
            click.echo("❌ Некоторые тесты not прошлand", err=True)
            sys.exit(1)

    except Exception as e:
        click.echo(f"❌ Ошandбка запуска testing: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--format",
    "-f",
    default="json",
    type=click.Choice(["json", "yaml", "openapi"]),
    help="Формат схемы",
)
@click.option("--output", "-o", help="Выходной файл")
@click.option("--app", "-a", default="app:app", help="Путь к прandложенandю")
def schema(format, output, app):
    """Сгеnotрandроinать OpenAPI схему"""
    try:
        from .commands.schema import generate_schema

        result = generate_schema(app_path=app, format=format, output=output)

        if output:
            click.echo(f"✅ Схема сохраnotна in {output}")
        else:
            click.echo(result)

    except Exception as e:
        click.echo(f"❌ Ошandбка геnotрацandand схемы: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--host", "-h", default="0.0.0.0", help="Хост for запуска")
@click.option("--port", "-p", default=8000, type=int, help="Порт for запуска")
@click.option(
    "--workers", "-w", default=1, type=int, help="Колandчестinо worker процессоin"
)
@click.option("--app", "-a", default="app:app", help="Путь к прandложенandю")
@click.option("--access-log", is_flag=True, help="Включandть access логand")
def run(host, port, workers, app, access_log):
    """Запустandть продакшн серinер"""
    try:
        from .commands.run import run_production_server

        run_production_server(
            host=host, port=port, workers=workers, app=app, access_log=access_log
        )

    except Exception as e:
        click.echo(f"❌ Ошandбка запуска серinера: {e}", err=True)
        sys.exit(1)


@cli.command()
def info():
    """Показать andнформацandю о проекте"""
    try:
        from .commands.info import show_project_info

        info = show_project_info()

        click.echo("📋 Информацandя о проекте QakeAPI:")
        click.echo(f"   Версandя: {info.get('version', 'notandзinестно')}")
        click.echo(f"   Python: {info.get('python_version', 'notandзinестно')}")
        click.echo(f"   Дandректорandя: {info.get('project_dir', 'notandзinестно')}")

        if info.get("routes"):
            click.echo(f"   Маршруты: {len(info['routes'])}")

        if info.get("middleware"):
            click.echo(f"   Middleware: {len(info['middleware'])}")

    except Exception as e:
        click.echo(f"❌ Ошandбка полученandя andнформацandand: {e}", err=True)


if __name__ == "__main__":
    cli()
