"""Small helper shared by every form so fields get Bootstrap styling."""


class BootstrapFormMixin:
    """Adds Bootstrap CSS classes to all widgets. Use it first in a form's bases."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            kind = widget.__class__.__name__
            if kind in ("CheckboxInput",):
                css = "form-check-input"
            elif kind in ("Select", "SelectMultiple"):
                css = "form-select"
            elif kind == "CheckboxSelectMultiple":
                css = "form-check-input"
            else:
                css = "form-control"
            widget.attrs["class"] = f"{widget.attrs.get('class', '')} {css}".strip()
