from django.shortcuts import render

from .models import Department, TeamMember


def team_structure(request):
    # Two focused, indexed queries instead of filtering one big list in Python.
    board_members = (
        TeamMember.objects.filter(is_published=True, is_board_member=True)
        .select_related("department")
    )
    leadership = (
        TeamMember.objects.filter(is_published=True, is_leadership=True, is_board_member=False)
        .select_related("department")
    )
    units = (
        Department.objects.filter(is_active=True, category="unit")
        .prefetch_related("members")
    )
    return render(
        request,
        "public/structure.html",
        {"board_members": board_members, "leadership": leadership, "units": units},
    )
