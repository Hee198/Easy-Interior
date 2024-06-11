import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import json
import base64
import numpy as np

app = dash.Dash(__name__)

app.layout = html.Div([
    dcc.Graph(id='room-3d', config={'editable': True}),  # 3D 그래프를 표시할 곳
    html.Div([
        html.Label('방 크기 설정 (cm):'),
        html.Label('방 너비:'),
        dcc.Input(id='room-width', type='number', value=1000, placeholder="방 너비"),
        html.Label('방 깊이:'),
        dcc.Input(id='room-depth', type='number', value=600, placeholder="방 깊이"),
        html.Label('방 높이:'),
        dcc.Input(id='room-height', type='number', value=300, placeholder="방 높이"),
        html.Br(),
        html.Label('가구 선택:'),
        dcc.Dropdown(
            id='furniture-dropdown',
            options=[
                {'label': '침대', 'value': 'bed'},
                {'label': '책상', 'value': 'desk'},
                {'label': '의자', 'value': 'chair'}
            ],
            value='bed'
        ),
        html.Label('X 위치 (cm):'),
        dcc.Input(id='x-pos', type='number', value=100, placeholder="X 위치 (cm)"),
        html.Label('Y 위치 (cm):'),
        dcc.Input(id='y-pos', type='number', value=100, placeholder="Y 위치 (cm)"),
        html.Label('Z 위치 (cm):'),
        dcc.Input(id='z-pos', type='number', value=0, placeholder="Z 위치 (cm)"),
        html.Label('가구 너비 (cm):'),
        dcc.Input(id='width', type='number', value=100, placeholder="가구 너비 (cm)"),
        html.Label('가구 높이 (cm):'),
        dcc.Input(id='height', type='number', value=100, placeholder="가구 높이 (cm)"),
        html.Label('가구 깊이 (cm):'),
        dcc.Input(id='depth', type='number', value=100, placeholder="가구 깊이 (cm)"),
        html.Label('회전 각도:'),
        dcc.Input(id='rotation', type='number', value=0, placeholder="회전 각도"),
        html.Button('가구 추가', id='add-furniture', n_clicks=0),
        html.Button('마지막 가구 삭제', id='remove-furniture', n_clicks=0),
        html.Button('배치 저장', id='save-layout', n_clicks=0),
        dcc.Upload(
            id='upload-layout',
            children=html.Button('배치 불러오기'),
            multiple=False
        ),
        html.Div(id='upload-status')
    ])
])

furniture_data = {'furniture': []}

def is_collision(new_item, furniture_list):
    nx, ny, nz = new_item['x'], new_item['y'], new_item['z']
    nw, nh, nd = new_item['width'], new_item['height'], new_item['depth']
    
    for item in furniture_list:
        x, y, z = item['x'], item['y'], item['z']
        w, h, d = item['width'], item['height'], item['depth']
        
        if (nx < x + w and nx + nw > x and ny < y + h and ny + nh > y and nz < z + d and nz + nd > z):
            return True
    return False

@app.callback(
    Output('room-3d', 'figure'),
    [Input('add-furniture', 'n_clicks'),
     Input('remove-furniture', 'n_clicks'),
     Input('upload-layout', 'contents'),
     Input('room-3d', 'relayoutData')],
    [State('room-width', 'value'),
     State('room-depth', 'value'),
     State('room-height', 'value'),
     State('furniture-dropdown', 'value'),
     State('x-pos', 'value'),
     State('y-pos', 'value'),
     State('z-pos', 'value'),
     State('width', 'value'),
     State('height', 'value'),
     State('depth', 'value'),
     State('rotation', 'value')]
)
def update_room(add_clicks, remove_clicks, upload_contents, relayout_data, room_width, room_depth, room_height, furniture_type, x, y, z, width, height, depth, rotation):
    ctx = dash.callback_context

    if ctx.triggered:
        if 'add-furniture' in ctx.triggered[0]['prop_id']:
            new_item = {
                'type': furniture_type,
                'x': x,
                'y': y,
                'z': z,
                'width': width,
                'height': height,
                'depth': depth,
                'rotation': rotation
            }
            if not is_collision(new_item, furniture_data['furniture']):
                furniture_data['furniture'].append(new_item)
        elif 'remove-furniture' in ctx.triggered[0]['prop_id']:
            if furniture_data['furniture']:
                furniture_data['furniture'].pop()
        elif 'upload-layout' in ctx.triggered[0]['prop_id']:
            content_type, content_string = upload_contents.split(',')
            decoded = base64.b64decode(content_string)
            furniture_data.update(json.loads(decoded.decode('utf-8')))
        elif 'relayoutData' in ctx.triggered[0]['prop_id'] and 'scene.annotations' in relayout_data:
            annotations = relayout_data['scene.annotations']
            for annotation in annotations:
                if 'text' in annotation:
                    for item in furniture_data['furniture']:
                        if item['type'] == annotation['text']:
                            item['x'] = annotation['x']
                            item['y'] = annotation['y']
                            item['z'] = annotation['z']

    fig = go.Figure()

    fig.add_trace(go.Mesh3d(
        x=[0, 0, room_width, room_width, 0, 0, room_width, room_width],
        y=[0, room_depth, room_depth, 0, 0, room_depth, room_depth, 0],
        z=[0, 0, 0, 0, room_height, room_height, room_height, room_height],
        color='lightgrey',
        opacity=0.50
    ))

    for item in furniture_data['furniture']:
        w, h, d = item['width'], item['height'], item['depth']
        color = 'blue' if item['type'] == 'bed' else 'green' if item['type'] == 'desk' else 'red'

        vertices = np.array([
            [item['x'], item['y'], item['z']],
            [item['x'] + w, item['y'], item['z']],
            [item['x'] + w, item['y'] + d, item['z']],
            [item['x'], item['y'] + d, item['z']],
            [item['x'], item['y'], item['z'] + h],
            [item['x'] + w, item['y'], item['z'] + h],
            [item['x'] + w, item['y'] + d, item['z'] + h],
            [item['x'], item['y'] + d, item['z'] + h]
        ])

        faces = np.array([
            [0, 1, 2, 3],  # Bottom face
            [4, 5, 6, 7],  # Top face
            [0, 1, 5, 4],  # Front face
            [2, 3, 7, 6],  # Back face
            [1, 2, 6, 5],  # Right face
            [3, 0, 4, 7]   # Left face
        ])

        i, j, k = [], [], []
        for face in faces:
            i.extend([face[0], face[1], face[2], face[0], face[2], face[3]])
            j.extend([face[1], face[2], face[3], face[0], face[1], face[3]])
            k.extend([face[2], face[3], face[0], face[1], face[2], face[0]])

        fig.add_trace(go.Mesh3d(
            x=vertices[:, 0],
            y=vertices[:, 1],
            z=vertices[:, 2],
            i=i,
            j=j,
            k=k,
            color=color,
            opacity=0.75,
            name=item['type']
        ))

        fig.add_trace(go.Scatter3d(
            x=[item['x'] + w / 2],
            y=[item['y'] + d / 2],
            z=[item['z'] + h / 2],
            text=[item['type']],
            mode='text'
        ))

    fig.update_layout(scene=dict(
        xaxis=dict(nticks=10, range=[0, room_width]),
        yaxis=dict(nticks=10, range=[0, room_depth]),
        zaxis=dict(nticks=10, range=[0, room_height]),
    ))

    return fig

@app.callback(
    Output('upload-status', 'children'),
    Input('save-layout', 'n_clicks')
)
def save_layout(n_clicks):
    if n_clicks > 0:
        with open('layout.json', 'w') as f:
            json.dump(furniture_data, f)
        return '배치가 저장되었습니다.'
    return ''

if __name__ == '__main__':
    app.run_server(debug=True)
