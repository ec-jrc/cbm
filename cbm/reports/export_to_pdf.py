#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD


import io
import glob
import os.path
import subprocess
import matplotlib.pyplot as plt
import cbm


def with_pdfme(aoi, year, pid, ptype='', notes={}, params={}, folder='',
               fname=None):
    """
    Example parcel report generator requares pdfme library
    """
    try:
        from pdfme import build_pdf
    except Exception as err:
        return err

    def fig2img(figcbm):
        plt.cla()   # Clear axis
        plt.clf()   # Clear figure
        plt.close()
        buf = io.BytesIO()
        figcbm.savefig(buf, format='png')
        return buf

    parcel_info = cbm.get.parcel_info.by_pid(aoi, year, pid, ptype)
    fig_parcel_info = fig2img(cbm.show.parcel_info.by_pid(
        aoi, year, pid, ptype, view=False))
    fig_time_series_s2 = fig2img(cbm.show.time_series.s2(
        aoi, year, pid, bands=['B02', 'B03', 'B04', 'B08'],
        scl='3_8_9_10_11', ptype=ptype, view=False))
    fig_time_series_ndvi = fig2img(cbm.show.time_series.ndvi(
        aoi, year, pid, ptype=ptype, view=False))
    fig_time_series_s1_bs = fig2img(cbm.show.time_series.s1(
        aoi, year, pid, 'bs', ptype, view=False))
    fig_time_series_s1_c6 = fig2img(cbm.show.time_series.s1(
        aoi, year, pid, 'c6', ptype, view=False))
    parcel_peers = cbm.get.parcels_list.peers(
        aoi, year, pid, distance=1000, maxPeers=5, ptype=ptype)
    # fig_time_series_ndvi_peers = fig2img(cbm.show.time_series.ndvi(
    #     aoi, year, parcel_peers['pids'], ptype=ptype))
    fig_time_series_ndvi_peers = fig2img(cbm.show.time_series.ndvi(
        aoi, year, [pid] + parcel_peers['pids'], ptype=ptype,
        max_line_plots=1, view=False))
    fig_time_series_s1_peers = fig2img(cbm.show.time_series.s1(
        aoi, year, [pid] + parcel_peers['pids'], 'bs', ptype,
        max_line_plots=1, view=False))

    document = {
        "style": {
            "margin_bottom": 15, "text_align": "j",
            "page_size": "letter", "margin": [60, 50]
        },
        "formats": {
            "url": {"c": "blue", "u": 1},
            "title": {"b": 1, "s": 13}
        },
        "running_sections": {
            "header": {
                "x": "left", "y": 20, "height": "top",
                "style": {"text_align": "r"},
                "content": [{".b": "This is a header"}]
            },
            "footer": {
                "x": "left", "y": 740, "height": "bottom",
                "style": {"text_align": "c"},
                "content": [{".": ["Page ", {"var": "$page"}]}]
            }
        },
        "sections": [
            {
                "style": {"page_numbering_style": "arabic"},
                "running_sections": ["footer"],
                "content": [

                    {
                        ".": "Example report", "style":
                        "title", "label": "title1",
                        "outline": {"level": 1, "text": "A different title 1"}
                    },

                    [
                        "Example parcel report for data retrieved from the RESTful API for CbM ",
                        ", For more details see the documentation at: ",
                        {".": "jrc-cbm.readthedocs.io", "style": "url",
                            "uri": "https://jrc-cbm.readthedocs.io"},
                    ],

                    {
                        "widths": [1.5, 7],
                        "style": {"s": 9},
                        "table": [
                            [
                                {
                                    "colspan": 1,
                                    "style": {
                                        "cell_fill": [0.5, 0.5, 0.5],
                                        "text_align": "c", "cell_margin": 8
                                    },
                                    ".b;c:1;s:16": aoi.upper(),
                                },
                                {
                                    "colspan": 1,
                                    "style": {
                                        "cell_fill": [0.57, 0.8, 0.3],
                                        "text_align": "c", "cell_margin_top": 13
                                    },
                                    ".b;c:1;s:12": parcel_info['cropname']
                                }
                            ],
                            [
                                {"colspan": 2, "image": fig_parcel_info,
                                 "image_name": "fig_parcel_info",
                                 "extension": "png"}, None
                            ],
                            [
                                {"colspan": 2,
                                 "style": {
                                     "text_align": "l",
                                 }, "content": [[notes['general']]]}, None
                            ],
                        ]
                    },
                    {"image": fig_time_series_s2,
                        "image_name": "fig_time_series_s2",
                        "extension": "png"},
                    {"image": fig_time_series_ndvi,
                        "image_name": "fig_time_series_ndvi",
                        "extension": "png"},
                    {"image": fig_time_series_s1_bs,
                        "image_name": "fig_time_series_s1_bs",
                        "extension": "png"},
                    {"image": fig_time_series_s1_c6,
                        "image_name": "fig_time_series_s1_c6",
                        "extension": "png"},
                    {"image": fig_time_series_ndvi_peers,
                        "image_name": "fig_time_series_ndvi_peers",
                        "extension": "png"},
                    {"image": fig_time_series_s1_peers,
                        "image_name": "fig_time_series_s1_peers",
                        "extension": "png"},
                ]
            },

        ]
    }

    if not fname:
        fname = f"{folder}/report_{aoi}_{year}_{pid}.pdf"
    else:
        fname = f"{folder}/{fname}"
    with open(fname, 'wb') as f:
        build_pdf(document, f)
    return f"Report generated, '{fname}'"


def from_notebook(with_code=False, nb_fname=None, debug=False):
    """
    Create pdf report for a given notebook, if this runs in a notebook cell
        will generate a pdf report for the runninig notebook.
    with_code: show code cels or not
    nb_fname: notebook name (optional)
    """

    def save():
        from IPython.display import Javascript, display
        return display(Javascript(
            "document.body.dispatchEvent("
            "new KeyboardEvent('keydown', {key:'s', keyCode: 83, ctrlKey: true}"
            "))"
        ))

    def isnotebook():
        try:
            shell = get_ipython().__class__.__name__
            if shell == 'ZMQInteractiveShell':
                return True   # Jupyter notebook or qtconsole
            elif shell == 'TerminalInteractiveShell':
                return False  # Terminal running IPython
            else:
                return False  # Other type (?)
        except NameError:
            return False

    def run_convert(with_code, nb_fname, debug):
        no_input = "" if with_code else "--no-input"
        try:
            if debug:
                print(f"Creating pdf from the notebook '{nb_fname}.ipynb' ...")
            subprocess.run(
                ["jupyter", "nbconvert", "--to", "pdf",
                 "--RegexRemovePreprocessor.patterns", "remove_cell",
                 no_input, nb_fname])
            pdfs = glob.glob('*.pdf')
            if (f'{nb_fname}.pdf' in pdfs):
                print(
                    f"Document generated from the notebook '{nb_fname}.ipynb'")
                return
            else:
                print("[Err]: Clould not create pdf. Check notebook content.")
                print("[Note]: links for external images e.g: '![Image](https://...image.png)'",
                      "and some special character combinations are not allowed.")
                return
        except Exception as err:
            if debug:
                return ("[Err] Could not create pdf report ", err)

    def with_widgets(debug):
        import ipywidgets as widgets
        from IPython.display import display

        ipynbs = [nb.split('.')[0] for nb in glob.glob('*.ipynb')]
        label = widgets.HTML("""Select a notebook from the list and run the
        conversion to PDF. <br> Add 'remove_cell = True' at the first line of
        each cell you do not want to include in the exported file.""")
        dropdown = widgets.Dropdown(options=ipynbs)
        button = widgets.Button(
            description='Export to PDF', tooltip='Export to PDF', icon='play')
        checkbox = widgets.Checkbox(
            description='With code cells', indent=False)
        output = widgets.Output()

        box = widgets.VBox(
            [label, widgets.HBox([dropdown, button, checkbox]), output])

        def on_button_clicked(b):
            output.clear_output()
            with output:
                save()
                run_convert(checkbox.value, dropdown.value, debug)

        button.on_click(on_button_clicked)

        return display(box)

    if not nb_fname or not os.path.isfile(nb_fname):
        if not isnotebook():
            return "Not running in a Notebook, please provide notebook name"
        else:
            save()
            try:
                import ipynbname
                nb_fname = ipynbname.name()
                run_convert(with_code, nb_fname, debug)
            except Exception as err:
                if debug:
                    print("Could not get the notebook name,", err)
                try:
                    with_widgets(True)
                except Exception as err:
                    return err
    else:
        if os.path.isfile(nb_fname):
            return run_convert(with_code, nb_fname, debug)
        else:
            return "Please provide a valid notebook name"


if __name__ == "__main__":
    import sys
    with_pdfme(sys.argv)
