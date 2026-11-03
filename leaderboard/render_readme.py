"""Render report-version README tables from results.json (standard library only)."""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
COLORS = ['#a16207', '#2563eb', '#f97316', '#16a34a', '#7c3aed', '#e11d48', '#0f766e', '#64748b']
HEADERS = [['PhysCapBench', 'Score'], ['Event', 'coverage'], ['Objects', 'and roles'], ['Actions', 'and motion'], ['Contact', 'and interaction'], ['States', 'and outcomes'], ['Physical mechanisms', 'and causality'], ['Temporal', 'order']]

def render(snapshot, domain):
    rows = sorted(snapshot['domains'][domain]['results'], key=lambda r: -r['overall'])
    keys = list(snapshot['dimension_labels'])
    width, model_width, rank_width, metric_width = 1450, 266, 64, 140
    top, header, group, row_height = 82, 70, 30, 58
    bottom = top + header + group + len(rows) * row_height
    height = bottom + 54
    label = snapshot['domains'][domain]['label']
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">', f'<title id="title">{label} PhysCapBench leaderboard</title>', '<desc id="desc">Report-version scores, fixed overall ranking and per-dimension competition ranks. Higher is better. Text tables are available in the README.</desc>', '<rect width="100%" height="100%" fill="#fff"/>', '<g font-family="Arial, Helvetica, sans-serif" fill="#20262b">']
    def text(x, y, value, size=16, color='#20262b', anchor='start', weight='400'):
        svg.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" text-anchor="{anchor}" font-weight="{weight}">{html.escape(str(value))}</text>')
    def medal(x, y, rank, large=False):
        radius = 12 if large else 9
        color = ['#d5a52d', '#96a2ad', '#ba8056'][rank-1]
        svg.append(f'<path d="M{x-6} {y-6} l-3 -13 8 2 3 11 M{x+6} {y-6} l3 -13 -8 2 -3 11" fill="{color}" opacity=".65"/>')
        svg.append(f'<circle cx="{x}" cy="{y}" r="{radius}" fill="{color}"/>')
        text(x, y+4, rank, 12 if large else 10, '#fff', 'middle', '700')
    text(0, 33, f'{label} Leaderboard', 28, weight='700')
    text(0, 61, 'Report-version results · Scores 0–100 · Higher is better', 14, '#737b83')
    text(width-2, 34, f'{len(rows)} strategies', 14, '#737b83', 'end')
    svg.append(f'<rect y="{top}" width="{width}" height="{header}" fill="#f1f3f5"/>')
    text(16, top+42, 'Model', 15, weight='700'); text(model_width+rank_width/2, top+42, '#', 15, anchor='middle')
    for j, lines in enumerate(HEADERS):
        x=model_width+rank_width+j*metric_width
        for k, line in enumerate(lines): text(x+metric_width/2, top+28+k*19, line, 13, anchor='middle')
        svg.append(f'<rect x="{x}" y="{top+header-3}" width="{metric_width}" height="3" fill="{COLORS[j]}"/>')
    svg.append(f'<rect y="{top+header}" width="{model_width+rank_width}" height="{group}" fill="#e9edf0"/>')
    text(16, top+header+21, f'Top {len(rows)}', 13, '#36414a')
    values=[[r['overall'], *[r['dimensions'][k] for k in keys]] for r in rows]
    for i, (r, vals) in enumerate(zip(rows, values)):
        y=top+header+group+i*row_height; mid=y+row_height/2
        if i%2: svg.append(f'<rect y="{y}" width="{width}" height="{row_height}" fill="#fafbfc"/>')
        text(16, mid+5, r['strategy'], 16)
        ranks=[1+sum(v[j]>value for v in values) for j,value in enumerate(vals)]
        if ranks[0]<=3: medal(model_width+rank_width/2, mid, ranks[0], True)
        else: text(model_width+rank_width/2, mid+5, ranks[0], 14, '#69737b', 'middle')
        for j,(value,rank) in enumerate(zip(vals,ranks)):
            x=model_width+rank_width+j*metric_width
            if rank<=3: medal(x+18, mid, rank)
            text(x+32, mid+4, f'#{rank}', 11, '#69737b')
            text(x+metric_width-13, mid+6, f'{value:.2f}', 17, '#6b4500' if j==0 else '#20262b', 'end', '600' if j==0 else '400')
        svg.append(f'<path d="M0 {y+row_height} H{width}" stroke="#e1e5e8"/>')
    for x in [0,model_width,model_width+rank_width,*[model_width+rank_width+(i+1)*metric_width for i in range(8)]]:
        svg.append(f'<path d="M{x} {top} V{bottom}" stroke="#e1e5e8"/>')
    text(0,bottom+32,'Overall scores retain the reported per-video aggregation. Equal scores share the same rank.',13,'#737b83')
    svg.append('</g></svg>')
    return '\n'.join(svg)+'\n'

if __name__ == '__main__':
    snapshot=json.loads((ROOT/'results.json').read_text())
    for domain in ['third','ego']:
        (ROOT/f'{domain}.svg').write_text(render(snapshot,domain))
