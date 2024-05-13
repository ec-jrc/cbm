import ipywidgets as widgets

def define_infobutton_style():
    style_html = """
<style>
    .info-button-style {
        border-radius: 50%;  /* Makes the button circular */
    }
    .info-button-style:hover {
        box-shadow: none !important;  /* Removes shadow on hover */
        transform: none !important;  /* Stops any popping or scaling */
        cursor: default;  /* Removes the hand cursor */
    }
</style>
"""
    return style_html


def create_text_entry(description, placeholder, width='500px'):
    """
    Create a text entry widget using the ipywidgets library with customizable description, placeholder, and width.

    Args:
    description (str): Label displayed next to the text box explaining its use.
    placeholder (str): Placeholder text displayed inside the text box when empty.
    width (str, optional): Width of the text box, specified as a CSS-like string (e.g., '500px'). Defaults to '500px'.

    Returns:
    ipywidgets.Combobox: Configured text entry widget.
    """
    return widgets.Combobox(
        placeholder=placeholder,
        description=description,
        ensure_option=False,
        disabled=False,
        style={"description_width": "initial"},
        layout=widgets.Layout(width=width)
    )

def create_int_entry(description, placeholder, min, max, width='500px'):
    """
    Create an integer entry widget with specified range and display properties.

    Args:
    description (str): Text describing the widget.
    placeholder (str): Placeholder text displayed in the widget.
    min (int): Minimum value the widget allows.
    max (int): Maximum value the widget allows.
    width (str, optional): Width of the widget, specified in CSS units. Defaults to '500px'.

    Returns:
    ipywidgets.BoundedIntText: Configured bounded integer entry widget.
    """
    return widgets.BoundedIntText(
        placeholder=placeholder,
        description=description,
        min=min,
        max=max,
        style={"description_width": "initial"},
        layout=widgets.Layout(width=width)
    )

def create_button(description, button_style, tooltip, color='#1daee3'):
    """
    Create a button widget with customizable styling options.

    Args:
    description (str): Text displayed on the button.
    button_style (str): Style of the button (e.g., 'success', 'info', 'warning', 'danger').
    tooltip (str): Tooltip text that appears when the user hovers over the button.
    color (str, optional): Background color of the button, specified as a hex code. Defaults to '#1daee3'.

    Returns:
    ipywidgets.Button: Configured button widget.
    """
    return widgets.Button(
        description=description,
        button_style=button_style,
        tooltip=tooltip,
        style={"button_color": color}
    )

def create_info_button(tooltip, css_class="info-button-style"):
    """
    Create an information button with a predefined style and a tooltip.

    Args:
    tooltip (str): Text displayed as a tooltip when the user hovers over the button.
    css_class (str, optional): CSS class to be applied for styling. Defaults to "info-button-style".

    Returns:
    ipywidgets.Button: Styled button with an information icon.
    """
    button = widgets.Button(
        icon="info",
        layout=widgets.Layout(width="30px"),
        button_style='',
        tooltip=tooltip
    )
    button.add_class(css_class)
    return button