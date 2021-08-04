import dash_html_components as html

def render_update_header(va_stats):
    header = html.Div(className="row", id="va_stats_header", children=[])
    if va_stats:
        assert "last_update" in va_stats and "last_submission" in va_stats
        if va_stats["last_update"] or va_stats["last_submission"]:
            if va_stats["last_update"]:
                update_desc = html.P(children=[html.I("Last Data Update: "), html.I(va_stats["last_update"])], style={"margin-left": "20px"})
                header.children.append(update_desc)
            if va_stats["last_submission"]:
                submission_desc = html.P(children=[html.I("Last VA Submission: "), html.I(va_stats["last_submission"])], style={"margin-left": "10px"})
                header.children.append(submission_desc)
    return header