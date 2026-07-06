"""
Small factory that generates a (List, Create, Update, Delete) view set for a
model, so the many content types the dashboard manages don't each need
hand-written boilerplate. Every generated view still goes through an access
mixin, CSRF-protected forms, and paginated, indexed querysets.
"""
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from core.i18n import SUPPORTED_LANGUAGES

from .mixins import OwnerActionLogMixin, StaffRequiredMixin, SuperAdminRequiredMixin


def group_form_fields(form):
    """
    Splits a ModelForm's fields into (base_fields, lang_fields) so templates
    can render `field_en`/`field_tet`/`field_pt` trios as language tabs
    instead of one long flat list.
    """
    base_fields = []
    lang_fields = {code: [] for code in SUPPORTED_LANGUAGES}
    for name in form.fields:
        matched = False
        for code in SUPPORTED_LANGUAGES:
            suffix = f"_{code}"
            if name.endswith(suffix):
                lang_fields[code].append(name)
                matched = True
                break
        if not matched:
            base_fields.append(name)
    return base_fields, lang_fields


def build_crud_views(*, model, form_class, url_namespace, template_folder, list_display=None, paginate_by=20, search_fields=None, ordering=None, superadmin_only=False):
    """
    Returns a dict with 'list', 'create', 'update', 'delete' CBV classes
    pre-wired for the given model. Pass superadmin_only=True to restrict
    the whole set (e.g. staff account management) to super admins.

    NOTE: class-body statements don't close over the enclosing function's
    locals the way nested *functions* do, so every value used at class-body
    level (not inside a method) is captured under a distinct `_xxx` name
    first to avoid `NameError: name 'model' is not defined`.
    """
    _model = model
    _form_class = form_class
    _paginate_by = paginate_by
    _list_display = list_display or []
    _url_namespace = url_namespace
    _template_folder = template_folder
    _search_fields = search_fields or []
    _ordering = ordering or []
    AccessMixin = SuperAdminRequiredMixin if superadmin_only else StaffRequiredMixin

    class _List(AccessMixin, ListView):
        model = _model
        template_name = f"dashboard/{_template_folder}/list.html"
        context_object_name = "objects"
        paginate_by = _paginate_by

        def get_queryset(self):
            qs = _model.objects.all()
            if _ordering:
                qs = qs.order_by(*_ordering)
            q = self.request.GET.get("q", "").strip()
            if q and _search_fields:
                from django.db.models import Q
                filt = Q()
                for f in _search_fields:
                    filt |= Q(**{f"{f}__icontains": q})
                qs = qs.filter(filt)
            return qs

        def get_context_data(self, **kwargs):
            ctx = super().get_context_data(**kwargs)
            ctx["list_display"] = _list_display
            ctx["url_namespace"] = _url_namespace
            ctx["search_query"] = self.request.GET.get("q", "")
            ctx["model_verbose"] = _model._meta.verbose_name_plural
            return ctx

    class _Create(AccessMixin, OwnerActionLogMixin, CreateView):
        model = _model
        form_class = _form_class
        template_name = f"dashboard/{_template_folder}/form.html"
        success_url = reverse_lazy(f"dashboard:{_url_namespace}_list")

        def form_valid(self, form):
            response = super().form_valid(form)
            messages.success(self.request, f"{_model._meta.verbose_name} created.")
            return response

        def get_context_data(self, **kwargs):
            ctx = super().get_context_data(**kwargs)
            ctx["url_namespace"] = _url_namespace
            ctx["mode"] = "create"
            ctx["model_verbose"] = _model._meta.verbose_name
            ctx["base_fields"], ctx["lang_fields"] = group_form_fields(ctx["form"])
            return ctx

    class _Update(AccessMixin, UpdateView):
        model = _model
        form_class = _form_class
        template_name = f"dashboard/{_template_folder}/form.html"
        success_url = reverse_lazy(f"dashboard:{_url_namespace}_list")

        def form_valid(self, form):
            response = super().form_valid(form)
            messages.success(self.request, f"{_model._meta.verbose_name} updated.")
            return response

        def get_context_data(self, **kwargs):
            ctx = super().get_context_data(**kwargs)
            ctx["url_namespace"] = _url_namespace
            ctx["mode"] = "update"
            ctx["model_verbose"] = _model._meta.verbose_name
            ctx["base_fields"], ctx["lang_fields"] = group_form_fields(ctx["form"])
            return ctx

    class _Delete(AccessMixin, DeleteView):
        model = _model
        template_name = "dashboard/confirm_delete.html"
        success_url = reverse_lazy(f"dashboard:{_url_namespace}_list")

        def form_valid(self, form):
            messages.success(self.request, f"{_model._meta.verbose_name} deleted.")
            return super().form_valid(form)

        def get_context_data(self, **kwargs):
            ctx = super().get_context_data(**kwargs)
            ctx["url_namespace"] = _url_namespace
            return ctx

    return {"list": _List, "create": _Create, "update": _Update, "delete": _Delete}
