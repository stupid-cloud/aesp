from nicegui import ui
import math
from pymatgen.core.periodic_table import Element
import itertools
import json
import os
from pymatgen.io.ase import AseAtomsAdaptor
import plotly.graph_objects as go
from pymatgen.analysis.diffraction.xrd import XRDCalculator


def show_atoms_info(candi):
    with ui.grid(columns=2).classes('w-full'):
        with ui.column():
            columns = [{'headerName': 'properties', 'field': "properties"}, {'properties': 'value', 'field': 'value'}]
            rows = [{'properties': 'formula', "value": candi.formula}, 
                    #  {'properties': 'volume', "value": candi.volume},
                     {'properties': 'natoms', "value": candi.natoms}]
            if candi.toatoms().get_cell_lengths_and_angles()[0] != 0:
                rows.append({'properties': 'volume', "value": candi.volume})
            for k, v in candi.key_value_pairs.items():
                rows.append({'properties': k, "value": v})
            for k, v in candi.data.items():
                rows.append({'properties': k, "value": v})
           
            ui.aggrid({
                'defaultColDef': {'flex': 1},
                'columnDefs': columns,
                'rowData': rows
            }).classes('w-full').style('height: 550px')
        with ui.column():
            atoms = candi.toatoms(add_additional_information=True)
            with ui.row():
                ui.label("Download").classes('text-xl').style("align-self:center; display:block;")
                
                if atoms.get_cell_lengths_and_angles()[0] != 0:
                    struc = AseAtomsAdaptor.get_structure(atoms)
                    rst1 = struc.to(fmt='cif')
                    ui.button('cif', on_click=lambda: ui.download(rst1.encode('utf-8'), f'{atoms.info["key_value_pairs"]["s_id"]}.cif'))
                    rst2 = struc.to(fmt='poscar')
                    ui.button('poscar', on_click=lambda: ui.download(rst2.encode('utf-8'), f'{atoms.info["key_value_pairs"]["s_id"]}.vasp')) 
                else:
                    struc = AseAtomsAdaptor.get_molecule(atoms)
                    rst1 = struc.to(fmt='gjf')
                    ui.button('gjf', on_click=lambda: ui.download(rst1.encode('utf-8'), f'{atoms.info["key_value_pairs"]["s_id"]}.gjf'))
                    rst = struc.to(fmt='xyz')
                    ui.button('xyz', on_click=lambda: ui.download(rst.encode('utf-8'), f'{atoms.info["key_value_pairs"]["s_id"]}.xyz'))
                
            if atoms.info["key_value_pairs"]['struc_type'] == 'bulk': 
                show_atoms(atoms, 2)
            elif atoms.info["key_value_pairs"]['struc_type'] == 'cluster':
                if atoms.get_cell_lengths_and_angles()[0] != 0:
                    show_atoms(atoms, 1)
                else:
                    show_atoms(atoms, 1, show_cell=False)
            columns = [{'headerName': 'axis', 'field': "axis"}, {'headerName': 'x [Å]', 'field': 'x'}, {'headerName': 'y [Å]', 'field': 'y'}, {'headerName': 'z [Å]', 'field': 'z'}]
            rows = []
            for i in range(3):
                rows.append({"axis": i+1, "x": float(atoms.cell[i][0]), "y": atoms.cell[i][1], "z": atoms.cell[i][2]})
            ui.aggrid({
                'defaultColDef': {'flex': 1},
                'columnDefs': columns,
                'rowData': rows
            }).classes('w-full').style("height: 130px")
            cell_info = atoms.cell.cellpar()
            with ui.grid(columns=4):
                ui.label("length (Å)")
                for i in cell_info[0:3]:
                    ui.label(i).classes()
                ui.label("angle (°)")
                for i in cell_info[3:6]:
                    ui.label(i).classes()
    ui.separator().props('color=orange size=16px')
    if atoms.info["key_value_pairs"]['struc_type'] == 'cluster':
        return 
    def show():
        struc = AseAtomsAdaptor.get_structure(candi.toatoms())
        xrd = XRDCalculator(wavelength=n1.value)
        dp = xrd.get_pattern(struc, two_theta_range=(n2.value, n3.value))
        # x_list = dp.x.tolist()
        trace_list = []
        for x, y in zip(dp.x, dp.y):
            trace = go.Scatter(
                x=[x, x],
                y=[0, y],
                mode='lines',
                showlegend=False
            )
            trace_list.append(trace)
        # del fig.data[0]
        fig.__init__(data=trace_list)
        # fig.update_layout(**layout)
        c_layout = go.Layout(
            title='2θ',
            font= {
                'family': 'Times New Roman',
                "size": 20
            },
            xaxis=dict(title='2θ (°)', range=[min(dp.x)-0.025*(max(dp.x)-min(dp.x)), max(dp.x)+0.025*(max(dp.x)-min(dp.x))]),
            yaxis=dict(title='Intensity')
        )
        fig.update_layout(c_layout)
        plot.update()

    with ui.row().style("align-self:center;"):   
        ui.label('XRD').classes('text-xl').style("align-self:center; display:block;")
        n1 = ui.number(label='Wavelength (Å)', value=0.5)   
        n2 = ui.number(label='Min θ (°)', value=0)
        n3 = ui.number(label='Max θ (°)', value=90)
        ui.button('submit', on_click=show).style("align-self:center;")
    with ui.row().classes('w-full'):
        fig = go.Figure()
        c_layout = go.Layout(
            title='2θ',
            font= {
                'family': 'Times New Roman',
                "size": 20
            },
            xaxis=dict(title='2θ (°)'),
            yaxis=dict(title='Intensity')
        )
        fig.update_layout(c_layout)
        plot = ui.plotly(fig).classes('w-full h-400')

    ui.separator()
    def show1():
        struc = AseAtomsAdaptor.get_structure(candi.toatoms())
        xrd = XRDCalculator(wavelength=n4.value)
        theta = [math.asin(n4.value/n5.value)*180/math.pi, math.asin(n4.value/n6.value)*180/math.pi]
        dp = xrd.get_pattern(struc, two_theta_range=(min(theta), max(theta)))
        x_list = [n4.value/math.sin(i*math.pi/180) for i in dp.x]
        trace_list = []
        for x, y in zip(x_list, dp.y):
            trace = go.Scatter(
                x=[x, x],
                y=[0, y],
                mode='lines',
                showlegend=False
            )
            trace_list.append(trace)
        # del fig.data[0]
        fig1.__init__(data=trace_list)
        # fig1.update_layout(**layout)
        c_layout = go.Layout(
            title='d-spacing',
            font= {
                'family': 'Times New Roman',
                "size": 20
            },
            xaxis=dict(title='d-spacing (Å)', range=[min(x_list)-0.025*(max(x_list)-min(x_list)), max(x_list)+0.025*(max(x_list)-min(x_list))]),
            yaxis=dict(title='Intensity')
        )
        fig1.update_layout(c_layout)
        plot1.update()
        
    with ui.row().style("align-self:center;"): 
        ui.label('XRD').classes('text-xl').style("align-self:center; display:block;")
        n4 = ui.number(label='d-spacing (Å)', value=0.5)   
        n5 = ui.number(label='Min d-spacing (Å)', value=n4.value)
        n6 = ui.number(label='Max d-spacing (Å)', value=50)
        ui.button('submit', on_click=show1).style("align-self:center;")

    with ui.row().classes('w-full'):
        fig1 = go.Figure()
        # fig1.update_layout(**layout)
        c_layout = go.Layout(
            title='d-spacing',
            font= {
                'family': 'Times New Roman',
                "size": 20
            },
            xaxis=dict(title='d-spacing (Å)'),
            yaxis=dict(title='Intensity')
        )
        fig1.update_layout(c_layout)
        plot1 = ui.plotly(fig1).classes('w-full h-400')

def atoms_to_rgb(element):
    python_path = os.path.dirname(__file__)
    with open(f"{python_path}/element_color.json", 'r') as f:
        data = json.load(f)
    return "rgb({r},{g},{b})".format(r=data[element][0], g=data[element][1], b=data[element][2])

def show_atoms(atoms, repeat=2, show_cell=True):
    atoms = atoms.copy()
    with ui.scene(background_color='#fff', grid=False, camera=ui.scene.orthographic_camera(size=25)).classes('w-full h-3/6') as scene:
        scene.axes_helper()
        # scene.sphere().material('#4488ff').move(2, 2, 2)
        # scene.cylinder(1, 0.5, 2, 20).material('#ff8800', opacity=0.5).move(-2, 1)
        # scene.extrusion([[0, 0], [0, 1], [1, 0.5]], 0.1).material('#ff8888').move(2, -1)
        cell = atoms.copy().cell
        atoms *= repeat
        # input()
        # with scene.group().move(z=2):
        #     scene.box().move(x=2)
        #     scene.box().move(y=2).rotate(0.25, 0.5, 0.75)
        #     scene.box(wireframe=True).material('#888888').move(x=2, y=2)
        # print(cell)
        # print(positions)
        if show_cell:
            m = (atoms.cell[0]+atoms.cell[1]+atoms.cell[2]) * 0.5
            scene.move_camera(look_at_x=m[0], look_at_y=m[1], look_at_z=m[2])
            # print(scene.get_camera())
            scene.line([0, 0, 0],cell[0]).material('#000000')
            scene.line([0, 0, 0], cell[1]).material('#000000')
            scene.line([0, 0, 0], cell[2]).material('#000000')
            # scene.curve([-4, 0, 0], [-4, -1, 0], [-3, -1, 0], [-3, 0, 0]).material('#008800')
            start_list = []
            for i in itertools.combinations([0, 1, 2], 2):
                end = cell[i[0]] + cell[i[1]]
                for j in i:
                    start = cell[j]
                    scene.line(start, end).material('#000000')
                start = end
                end = cell[0] + cell[1] + cell[2]
                scene.line(start, end).material('#000000')
        else:
            scene.move_camera(look_at_x=0, look_at_y=0, look_at_z=0)
        for atom in atoms:
            atomic_radius = float(Element(atom.symbol).atomic_radius) / 2
            scene.sphere(radius=atomic_radius).material(atoms_to_rgb(atom.symbol)).move(atom.position[0], atom.position[1], atom.position[2])
    return scene