import datetime
import time

import click
from click import get_current_context

from valohai_cli.api import request
from valohai_cli.consts import stream_styles
from valohai_cli.ctx import get_project
from valohai_cli.tui import Divider, Flex, Layout


class WatchTUI:
    status_styles = {
        'started': {'fg': 'blue', 'bold': True},
        'crashed': {'fg': 'white', 'bg': 'red'},
        'stopped': {'fg': 'red'},
        'completed': {'fg': 'green', 'bold': True},
    }

    def __init__(self, exec_detail_url):
        self.exec_detail_url = exec_detail_url

    def refresh(self):
        self.data = request('get', self.exec_detail_url).json()
        self.draw()

    def draw(self):
        execution = self.data
        events = execution.get('events', ())
        l = Layout()
        l.add(
            Flex(style={'bg': 'blue', 'fg': 'white'})
            .add(
                content='({project}) #{counter}'.format(project=execution['project']['name'], counter=execution['counter']),
                style={'bold': True},
            )
            .add(
                content=datetime.datetime.now().isoformat(),
                align='right',
            )
        )
        l.add(
            Flex()
            .add(
                'Status: {status}'.format(status=execution['status']),
                style=self.status_styles.get(execution['status'], {}),
            )
            .add('Step: {step}'.format(step=execution['step']))
            .add('Commit: {commit}'.format(commit=execution['commit']['identifier']))
            .add('{n} events'.format(n=len(events)), align='right')
        )
        l.add(Divider('='))

        available_height = l.height - len(l.rows) - 2
        if available_height > 0:
            for event in events[-available_height:]:
                l.add(
                    Flex(style=stream_styles.get(event['stream']))
                    .add(event['time'].split('T')[1][:-4] + '  ', flex=0)
                    .add(event['message'], flex=4)
                )
        click.clear()
        l.draw()


@click.command()
@click.argument('counter')
def watch(counter):
    """
    Watch execution progress in a console UI.
    """
    execution = get_project(require=True).get_execution_from_counter(counter=counter)
    tui = WatchTUI(execution['url'])
    try:
        while True:
            tui.refresh()
            time.sleep(1)
    except KeyboardInterrupt:
        get_current_context().exit()