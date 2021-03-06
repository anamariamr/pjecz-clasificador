import click
import configparser
import email
import imaplib
import os
import smtplib
import time
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication


class Config(object):

    def __init__(self):
        self.rama = ''
        self.servidor_imap = ''
        self.email_direccion = ''
        self.email_contrasena = ''
        self.deposito_ruta = ''


pass_config = click.make_pass_decorator(Config, ensure=True)


@click.group()
@click.option('--rama', default='', type=str, help='Acuerdos, Edictos o Sentencias')
@pass_config
def cli(config, rama):
    click.echo('Hola, ¡soy Clasificador!')
    # Rama
    if not rama.title() in ['Acuerdos', 'Edictos', 'Sentencias']:
        click.echo('ERROR: Rama no programada.')
        sys.exit(1)
    config.rama = rama.title()
    # Configuración
    settings = configparser.ConfigParser()
    settings.read('settings.ini')
    try:
        config.servidor_imap = settings['Global']['servidor_imap']
        config.email_direccion = settings[config.rama]['email_direccion']
        config.email_contrasena = settings[config.rama]['email_contrasena']
        config.deposito_ruta = settings[config.rama]['deposito_ruta']
    except KeyError:
        click.echo('ERROR: Falta configuración en settings.ini')
        sys.exit(1)
    # Validar
    if not config.servidor_imap:
        click.echo('ERROR: Falta el servidor_imap')
        sys.exit(1)
    if not config.email_direccion:
        click.echo('ERROR: Falta la email_direccion')
        sys.exit(1)
    if not config.email_contrasena:
        click.echo('ERROR: Falta la email_contrasena')
        sys.exit(1)
    if not config.deposito_ruta:
        click.echo('ERROR: Falta el deposito_ruta')
        sys.exit(1)
    if not os.path.exists(config.deposito_ruta) or not os.path.isdir(config.deposito_ruta):
        click.echo(f'ERROR: No existe o no es directorio {config.deposito_ruta}')
        sys.exit(1)


def cargar_inbox(config):
    """ Cargar carpeta inbox del correo electrónico """
    mail = imaplib.IMAP4_SSL(config.servidor_imap)
    mail.login(config.email_direccion, config.email_contrasena)
    mail.list()
    mail.select('inbox') # Accesar la carpeta inbox
    inbox_tipo, inbox_datos = mail.search(None, 'UNSEEN') # Obtener mensajes sin leer
    inbox_ids = inbox_datos[0]
    id_list = inbox_ids.split()
    return(mail, inbox_datos)


@cli.command()
@pass_config
def informar(config):
    """ Informar con una línea breve en pantalla """
    click.echo('Voy a informar... nada aun.')


@cli.command()
@pass_config
def leer(config):
    """ Leer """
    click.echo('Voy a leer...')
    mail, inbox_datos = cargar_inbox(config)
    for item in inbox_datos[0].split(): # Recorre los mensajes sin leer
        mensaje_tipo, mensaje_datos = mail.fetch(item, '(RFC822)' )
        mensaje_crudo = mensaje_datos[0][1]
        mensaje_texto = mensaje_crudo.decode('utf-8')
        mensaje = email.message_from_string(mensaje_texto)
        # Mostrar
        click.echo(f'To:      {mensaje["To"]}')
        click.echo(f'From:    {mensaje["From"]}')
        click.echo(f'Subject: {mensaje["Subject"]}')
        click.echo(f'Date:    {mensaje["Date"]}')
        click.echo()


@cli.command()
@pass_config
def leer_clasificar(config):
    """ Leer y clasificar """
    click.echo('Voy a leer y clasificar...')
    mail, inbox_datos = cargar_inbox(config)
    for item in inbox_datos[0].split(): # Recorre los mensajes sin leer
        mensaje_tipo, mensaje_datos = mail.fetch(item, '(RFC822)' )
        mensaje_crudo = mensaje_datos[0][1]
        mensaje_texto = mensaje_crudo.decode('utf-8')
        mensaje = email.message_from_string(mensaje_texto)
        # PENDIENTE Determinar el subdirectorio en el depósito
        # FALTA la ruta relativa según el remitente
        destino_ruta = config.deposito_ruta
        # PENDIENTE SI NO SE TIENE EL remitente se pasa al siguiente
        # Validar que exista el subdirectorio
        if not os.path.exists(destino_ruta) or not os.path.isdir(destino_ruta):
            click.echo(f'ERROR: No existe o no es directorio {destino_ruta}, se omite mensaje de {mensaje["From"]}')
            next
        # Bucle para las partes en el mensaje
        for parte in mensaje.walk():
            nombre = parte.get_filename()
            # Si es un archivo adjunto
            if bool(nombre):
                # PENDIENTE Validar que sea un archivo PDF
                # PENDIENTE Si no es PDF se pasa al siguiente
                # Guardar archivo adjunto
                archivo_ruta = os.path.join(destino_ruta, nombre)
                with open(archivo_ruta, 'wb') as puntero:
                    puntero.write(parte.get_payload(decode=True))


@cli.command()
@pass_config
def leer_clasificar_responder(config):
    """ Leer, clasificar y responder """
    click.echo('Voy a leer, clasificar y responder... nada aun.')


cli.add_command(informar)
cli.add_command(leer)
cli.add_command(leer_clasificar)
cli.add_command(leer_clasificar_responder)
