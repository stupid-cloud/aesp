from nicegui import ui
import pandas as pd
from pathlib import Path
import plotly.io as pio
from aesp.func.database import DataConnection
import os
import sys
from aesp.gui.atoms_info import show_atoms_info


path = Path(sys.argv[1])
dc = DataConnection(path.joinpath("generation.json"))

with ui.header().classes(replace='row items-center') as header:
    # ui.button(on_click=lambda: left_drawer.toggle(), icon='menu').props('flat color=white')
    # ui.image("./logo.png").classes('w-16 bg-none')
    with ui.tabs() as tabs:
        ui.tab('database')
        ui.tab('analysis')
        ui.tab('opt_params')

def update_database(value, result, grid):
    rows = []
    candis = list(dc.db.select(selection=value))
    columns = None
    for ar in candis:
        columns = [{'headerName': k, 'field': k} for k in ar.key_value_pairs.keys()]
        rows.append(ar.key_value_pairs)
    grid.options['rowData'] = rows
    grid.update()

def database():  
    with ui.row().classes('w-full'):
        ipt = ui.input(label='search', placeholder='query strings of ase.db').style("align-self:flex-end;").props('clearable rounded outlined')
        ui.button(on_click=lambda event: update_database(ipt.value, result, grid)).style("flex-direction:column; padding-left:0px; align-self:center;").props('outline round icon=navigation').classes('shadow-lg')
        result = ui.button("help", on_click=lambda: ui.navigate.to("https://wiki.fysik.dtu.dk/ase/ase/db/db.html#module-ase.db", new_tab=True)).style("align-self:center;")
        ui.space()
        ui.label('generation').style("align-self:center; display:flex; flex-direction:row; justify-content:center; align-items:end;")
        max_generation = dc.get_max_generation()
        max_stage = dc.get_max_stage(generation=1)
        ui.select([i+1 for i in range(max_generation)], value=1, on_change=lambda event: update_database('generation={}'.format(event.value), result, grid)).style("align-self:flex-start; display:block;")
        ui.space()
        ui.label('stage').style("align-self:center;")
        ui.select([i for i in range(max_stage+1)], value=0, on_change=lambda event: update_database('stage={}'.format(event.value), result, grid))
        # left_drawer.toggle()
    rows = []
    candis = dc.db.select()
    columns = None
    for ar in candis:
        columns = [{'headerName': k, 'field': k} for k in ar.key_value_pairs.keys()]
        rows.append(ar.key_value_pairs)

    grid = ui.aggrid({
        'defaultColDef': {'flex': 1},
        'columnDefs': columns,
        'rowData': rows
    }).classes("w-full").style("height:490px; align-self:center;")
    grid.options.update(pagination=True, paginationPageSize=15)
    grid.on('cellClicked', lambda event: ui.navigate.to(f"/atoms/{event.args['data']['s_id']}/{event.args['data']['stage']}", new_tab=True))


def opt_params():
    current_dir = path.joinpath('html/params')

    json_files = current_dir.glob('*.json')
    for file in json_files:
        with open(file, 'r') as f:
            f_josn = f.read()
        fig = pio.from_json(f_josn)
        ui.plotly(fig).style("align-self:center;").style("align-self:center;").style("align-self:center;").style("align-self:center;").style("align-self:center;")


def analysis():

    ui.label('Content of generation').classes("text-4xl").style("align-self:center; display:block;")
    current_dir = path.joinpath('html/')

    json_files = current_dir.glob('*generation.json')
    for file in json_files:
        with open(file, 'r') as f:
            f_josn = f.read()
        fig = pio.from_json(f_josn)
        ui.plotly(fig).style("align-self:center;")
    ui.separator().props('color=orange size=16px')
    ui.label('Content of population').classes("text-4xl").style("align-self:center;")
    json_files = current_dir.glob('*population.json')
    for file in json_files:
        with open(file, 'r') as f:
            f_josn = f.read()
        fig = pio.from_json(f_josn)
        ui.plotly(fig).style("align-self:center;").style("align-self:center;")
    ui.separator().props('color=orange size=16px')
    ui.label('Content of diversity').classes("text-4xl").style("align-self:center;")
    json_files = current_dir.glob('diversity.json')
    for file in json_files:
        with open(file, 'r') as f:
            f_josn = f.read()
        fig = pio.from_json(f_josn)
        ui.plotly(fig).style("align-self:center;")



with ui.tab_panels(tabs, value='database').classes('w-full h-full'):
    with ui.tab_panel('database'):
        
        database()
    with ui.tab_panel('analysis'):
        analysis()
    with ui.tab_panel('opt_params'):
        opt_params()

@ui.page('/atoms/{s_id}/{stage}')
def atoms_info_page(s_id, stage):
    candi = list(dc.db.select(s_id=int(s_id), stage=int(stage)))[0]
    show_atoms_info(candi)

ui.page_title('AESP')
# return ui
ui.run(on_air=True)