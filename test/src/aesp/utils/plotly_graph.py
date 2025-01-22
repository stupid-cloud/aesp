import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import plotly.colors
import numpy as np
import pandas as pd
from aesp.constant import operator


config = {
        'toImageButtonOptions': {
            'format': 'svg',
            'filename': 'my_plot',
            'scale': 2
        }
    }

layout = {
    "font" : {
        'family': 'Times New Roman',
        "size": 20
    },
    'width': 1000, 
    'height': 600,
    # "paper_bgcolor": 'rgba(0,0,0,0)',
    # "plot_bgcolor": 'rgba(0,0,0,0)',
    # "margin": dict(l=50, r=50, t=50, b=50),
    "xaxis": dict(showline=True, linecolor='black', linewidth=2, mirror=True, ticks='inside'),
    "yaxis": dict(showline=True, linecolor='black', linewidth=2, mirror=True, ticks='inside')   
}

def draw_ea(data, info_dict, path, key):
    
    data['opacity'] = 0.5
    # opt_line
    max_gen = data.iloc[:, 0].max()
    idx_list = []
    line_list = []
    min_e = np.inf
    for i in range(1, max_gen+1):
        temp_e = data[data.iloc[:, 0]==i]['fitness'].min()
        if temp_e < min_e:
            if i > 1:
                line_list.append(min_e)
                idx_list.append(i)  
            min_e = temp_e 
        line_list.append(min_e)
        idx_list.append(i)
    opt_line_trace = go.Scatter(
        x=idx_list,
        y=line_list,
        mode='lines',
        marker={'size': 5, "symbol": "star"},
        name='opt_line'
    )

    # operator
    operator_groups = data.groupby('oper_type') # ['generator', 'mutation', 'crossover', 'seed']
    operator_trace_list = []

    for group_name, group in operator_groups:
        trace = go.Scatter(
            x=group['gen.'],  
            y=group["fitness"],
            marker={'size': 10, "opacity": group['opacity']},
            mode='markers',
            name=group_name,
        )
        if group_name == 'seeds':
            continue
        trace_list1 = []
        operator_trace_list.append(trace)
        if len(info_dict[group_name][0]) >= 1:
            trace = go.Scatter(
                x=info_dict[group_name][0],  
                y=info_dict[group_name][1],
                marker={'size': 5, "symbol": 'diamond'},
                mode='lines+markers',
                line={"dash": 'dash'},
                name=group_name+'_mean',
                zorder=10
            )
            operator_trace_list.append(trace)
            trace_list1.append(trace)
        
        if group_name == 'mutation':
            o_groups = group.groupby('oper_name')
            mut_list = []
            for group_name1, group1 in o_groups:
                trace = go.Scatter(
                    x=group1['gen.'],  
                    y=group1["fitness"],
                    marker={'size': 10, "opacity": group1['opacity']},
                    mode='markers',
                    name=group_name1
                )
                trace_list1.append(trace)
                new_k = group_name1.split('->')
                mut_list += new_k

            mut_list = set(mut_list)
            for mut_name in mut_list:
                for name in [mut_name, mut_name+'_r']:
                    if info_dict.get(name) and len(info_dict[name][0]) >= 1:
                        trace = go.Scatter(
                            x=info_dict[name][0],  
                            y=info_dict[name][1],
                            marker={'size': 5, "symbol": 'diamond'},
                            mode='lines+markers',
                            line={"dash": 'dash'},
                            name=name+'_mean',
                            zorder=10
                        )
                        trace_list1.append(trace)
                        
            for name in ['single_mut', 'continuous_mut']:
                if info_dict.get(name) and len(info_dict[name][0]) >= 1:
                    trace = go.Scatter(
                        x=info_dict[name][0],  
                        y=info_dict[name][1],
                        marker={'size': 5, "symbol": 'diamond'},
                        mode='lines+markers',
                        line={"dash": 'dash'},
                        name=name+'_mean',
                        zorder=10
                    )
                    trace_list1.append(trace)
        else:
            o_groups = group.groupby('oper_name')
            for group_name1, group1 in o_groups:
                trace = go.Scatter(
                    x=group1['gen.'],  
                    y=group1["fitness"],
                    marker={'size': 10, "opacity": group1['opacity']},
                    mode='markers',
                    name=group_name1
                )
                trace_list1.append(trace)
            
                if len(info_dict[group_name1][0]) >= 1:
                    trace = go.Scatter(
                        x=info_dict[group_name1][0],  
                        y=info_dict[group_name1][1],
                        marker={'size': 5, "symbol": 'diamond'},
                        mode='lines+markers',
                        line={"dash": 'dash'},
                        name=group_name1+'_mean',
                        zorder=10
                    )
                    trace_list1.append(trace)

        trace_list1.append(opt_line_trace)
        fig = go.Figure(data=trace_list1)  
        fig.update_layout(**layout)
        if group_name == 'mutation':
            fig.update_layout({'width': 1000, 'height': 600})
        fig.update_layout(title=group_name, xaxis_title=key.capitalize(), yaxis_title='fitness')

        # 存储html
        pio.write_html(fig, path / f"{group_name}_{key}.html", config=config)
        # 存储json
        json_str = fig.to_json()
        with open(path / f"{group_name}_{key}.json", 'w') as f:
            f.write(json_str)
        # 存储csv
        csv_path = path / f"{group_name}_{key}"
        csv_path.mkdir(parents=True, exist_ok=True)
        for i, data in enumerate(fig.data):
            data_df = pd.DataFrame()
            data_df[key] = list(data.x)
            data_df[data.name] = list(data.y)
            data_df.to_csv(csv_path / f"{data.name}.csv", index=False)
        
    trace = go.Scatter(
            x=info_dict['operator'][0],  
            y=info_dict['operator'][1],
            marker={'size': 5, "symbol": 'diamond'},
            mode='lines+markers',
            line={"dash": 'dash'},
            name='operator_mean',
            zorder=10
        )
    operator_trace_list.append(trace)
    operator_trace_list.append(opt_line_trace)
    fig = go.Figure(data=operator_trace_list)
    fig.update_layout(**layout)
    fig.update_layout(title='operator', xaxis_title=key.capitalize(), yaxis_title='fitness')
    # 存储html
    pio.write_html(fig, path / f'operator_{key}.html', config=config)
    # 存储json
    json_str = fig.to_json()
    with open( path / f'operator_{key}.json', 'w') as f:
        f.write(json_str)
    # 存储csv
    csv_path = path / f'operator_{key}'
    csv_path.mkdir(parents=True, exist_ok=True)
    for i, data in enumerate(fig.data):
        data_df = pd.DataFrame()
        data_df[key] = list(data.x)
        data_df[data.name] = list(data.y)
        data_df.to_csv(csv_path / f"{data.name}.csv", index=False)
   

def draw_diversity(data, path):
    trace_list = []
    x_label = data.columns[0]
    marker_list = ["circle", 'diamond']
    for idx, y_label in enumerate(data.columns[1:]):
        trace = go.Scatter( 
            x=data[x_label],    
            y=data[y_label],  
            mode='lines+markers',
            marker={'size': 15, "symbol": marker_list[idx], 'color': plotly.colors.qualitative.Plotly[idx]},
            name=y_label, 
            line={'width': 5}
        )
        trace_list.append(trace)
    fig = go.Figure(data=trace_list)
    fig.update_layout(**layout)
    c_layout = go.Layout(
        title='diversity',
        xaxis=dict(title='Generation'),
        yaxis=dict(title='Diversity')
    )
    fig.update_layout(c_layout)
    pio.write_html(fig, path / 'diversity.html', config=config)
    # 存储json
    json_str = fig.to_json()
    with open( path / 'diversity.json', 'w') as f:
        f.write(json_str)

def draw_con_mut_factor(x_index, continuos_mut_factor, path):
    trace_list = []
    trace = go.Scatter( 
        x=x_index,    
        y=continuos_mut_factor,  
        mode='lines+markers',
        marker={'size': 15},
        name="continuos_mut_factor", 
        line={'width': 5}
    )
    trace_list.append(trace)
    fig = go.Figure(data=trace_list)
    fig.update_layout(**layout)
    c_layout = go.Layout(
        title='continuos_mut_factor',
        xaxis=dict(title='Gen.'),
        yaxis=dict(title='Factor')
    )
    fig.update_layout(c_layout)
    pio.write_html(fig, path / 'cmf.html', config=config)
    # 存储json
    json_str = fig.to_json()
    with open( path / 'cmf.json', 'w') as f:
        f.write(json_str)

def draw_size(data, path):
    trace_list = []
    marker_list = ["circle", 'diamond', 'star']
    x_label = data.columns[0]
    for idx, y_label in enumerate(data.columns[1:]):
        trace = go.Scatter( 
            x=data[x_label],    
            y=data[y_label],  
            mode='lines+markers',
            marker={'size': 15, "symbol": marker_list[idx], 'color': plotly.colors.qualitative.Plotly[idx]},
            name=y_label, 
            line={'width': 5}
        )
        trace_list.append(trace)
    fig = go.Figure(data=trace_list)
    fig.update_layout(**layout)
    c_layout = go.Layout(
        title='size',
        xaxis=dict(title='Gen. or Pop.'),
        yaxis=dict(title='Size')
    )
    fig.update_layout(c_layout)
    pio.write_html(fig, path / 'size.html', config=config)
    # 存储json
    json_str = fig.to_json()
    with open( path / 'size.json', 'w') as f:
        f.write(json_str)

def draw_prob(x_index, info, path, key):
    trace_list = []
    marker_list = ["circle", 'diamond', 'star']
    for idx, (k, v) in enumerate(info.items()):
        trace = go.Scatter( 
            x=x_index,    
            y=v,  
            mode='lines+markers',
            marker={'size': 15, "symbol": marker_list[idx], 'color': plotly.colors.qualitative.Plotly[idx]},
            name=k, 
            line={'width': 5}
        )
        trace_list.append(trace)
    fig = go.Figure(data=trace_list)
    fig.update_layout(**layout)
    c_layout = go.Layout(
        title=key,
        xaxis=dict(title='Generation'),
        yaxis=dict(title='Probability')
    )
    fig.update_layout(c_layout)
    pio.write_html(fig, path / f'{key}_prob.html', config=config)
    # 存储json
    json_str = fig.to_json()
    with open( path / f'{key}_prob.json', 'w') as f:
        f.write(json_str)
    # 存储csv
    csv_path = path / f'{key}_prob'
    csv_path.mkdir(parents=True, exist_ok=True)
    for i, data in enumerate(fig.data):
        data_df = pd.DataFrame()
        data_df[key] = list(data.x)
        data_df[data.name] = list(data.y)
        data_df.to_csv(csv_path / f"{data.name}.csv", index=False)