import csv
import itertools
import os
from operator import itemgetter
from pathlib import Path

from django.db.models import (
    Case,
    CharField,
    Count,
    DateField,
    F,
    OuterRef,
    Q,
    Subquery,
    Value,
    When,
)
from django.db.models.functions import Cast, Substr, TruncMonth

from va_explorer.va_data_management.models import (
    Location,
    questions_to_autodetect_duplicates,
)
from va_explorer.va_data_management.utils.loading import get_va_summary_stats


def load_cod_groupings(cause_of_death: str):
    INTERVA_GROUPCODE = os.environ.get("INTERVA_GROUPCODE") == "True"
    if INTERVA_GROUPCODE:
        filename = "cod_groupings_interva_groupcode_true.csv"
    else:
        filename = "cod_groupings_interva_groupcode_false.csv"
    path = Path(__file__).parent.parent / "data" / filename

    with open(path) as csvfile:
        filereader = csv.DictReader(csvfile)
        remove = ["algorithm", "cod"]
        headers = [header for header in filereader.fieldnames if header not in remove]

        data = []
        for row in filereader:
            data.append(row)

        cods = sorted([row.get("cod") for row in data] + headers)

    filter_causes = []
    if cause_of_death:
        for row in data:
            if row.get("cod") == cause_of_death:
                filter_causes.append(row.get("cod"))
                break

            for key, value in row.items():
                if cause_of_death == key and value == "1":
                    filter_causes.append(row.get("cod"))

    return {"dropdown_options": cods, "filter_causes": filter_causes}


# ============ VA Data =================
def load_va_data(
    user, cause_of_death, start_date, end_date, region_of_interest, age, sex
):
    user_vas = user.verbal_autopsies(date_cutoff=start_date, end_date=end_date)

    # get stats on last update and last va interview date
    update_stats = get_va_summary_stats(user_vas)
    if len(questions_to_autodetect_duplicates()) > 0:
        update_stats["duplicates"] = user_vas.filter(duplicate=True).count()

    user_vas_filtered = user_vas.exclude(Id10023__in=["dk", "DK"]).exclude(
        location__isnull=True
    )

    # apply cause of death filtering if sent in with request
    if cause_of_death:
        causes = load_cod_groupings(cause_of_death=cause_of_death)["filter_causes"]
        user_vas_filtered = user_vas_filtered.filter(causes__cause__in=causes)

    # apply geographic filtering if sent in with request
    if region_of_interest:
        if "District" in region_of_interest:
            user_vas_filtered = (
                user_vas_filtered.annotate(
                    district_name=Subquery(
                        Location.objects.values("name").filter(
                            Q(path=Substr(OuterRef("location__path"), 1, 12)),
                            Q(depth=3),
                        )[:1]
                    )
                )
                .filter(district_name=region_of_interest)
                .select_related("location")
            )

        if "Province" in region_of_interest:
            user_vas_filtered = (
                user_vas_filtered.annotate(
                    province_name=Subquery(
                        Location.objects.values("name").filter(
                            Q(path=Substr(OuterRef("location__path"), 1, 8)), Q(depth=2)
                        )[:1]
                    )
                )
                .filter(province_name=region_of_interest)
                .select_related("location")
            )

    # apply filtering for age sent in request, cover is<X>, is<X>1, and is<X>2
    # from VA specification
    if age:
        if age == "adult":
            user_vas_filtered = user_vas_filtered.filter(
                Q(isAdult="1")
                | Q(isAdult="1.0")
                | Q(isAdult1="1")
                | Q(isAdult1="1.0")
                | Q(isAdult2="1")
                | Q(isAdult2="1.0")
            )
        if age == "child":
            user_vas_filtered = user_vas_filtered.filter(
                Q(isChild="1")
                | Q(isChild="1.0")
                | Q(isChild1="1")
                | Q(isChild1="1.0")
                | Q(isChild2="1")
                | Q(isChild2="1.0")
            )
        if age == "neonate":
            user_vas_filtered = user_vas_filtered.filter(
                Q(isNeonatal="1")
                | Q(isNeonatal="1")
                | Q(isNeonatal1="1")
                | Q(isNeonatal1="1")
                | Q(isNeonatal2="1")
                | Q(isNeonatal2="1")
            )

    # apply filtering for sex sent in request
    if sex:
        user_vas_filtered = user_vas_filtered.filter(Id10019=sex)

    uncoded_vas = user_vas.filter(causes__cause__isnull=True).count()

    demographics = (
        user_vas_filtered.filter(causes__isnull=False)
        .values(
            gender=F("Id10019"),
            age_group_named=Case(
                When(isNeonatal="1", then=Value("neonate")),
                When(isNeonatal="1.0", then=Value("neonate")),
                When(isNeonatal1="1", then=Value("neonate")),
                When(isNeonatal1="1.0", then=Value("neonate")),
                When(isNeonatal2="1", then=Value("neonate")),
                When(isNeonatal2="1.0", then=Value("neonate")),
                When(isChild="1", then=Value("child")),
                When(isChild="1.0", then=Value("child")),
                When(isChild1="1", then=Value("child")),
                When(isChild1="1.0", then=Value("child")),
                When(isChild2="1", then=Value("child")),
                When(isChild2="1.0", then=Value("child")),
                When(isAdult="1", then=Value("adult")),
                When(isAdult="1.0", then=Value("adult")),
                When(isAdult1="1", then=Value("adult")),
                When(isAdult1="1.0", then=Value("adult")),
                When(isAdult2="1", then=Value("adult")),
                When(isAdult2="1.0", then=Value("adult")),
                default=Value("Unknown"),
                output_field=CharField(),
            ),
        )
        .annotate(count=Count("pk"))
        .order_by("age_group_named")
    )

    demographics = [
        {
            "age_group": key,
            **{item.get("gender"): item.get("count") for item in list(group)},
        }
        for key, group in itertools.groupby(demographics, itemgetter("age_group_named"))
    ]

    COD_sums = (
        user_vas_filtered.filter(causes__isnull=False)
        .select_related("causes")
        .values(cause=F("causes__cause"))
        .annotate(count=Count("pk"))
        .order_by("-count")
    )

    COD_trend = (
        user_vas_filtered.annotate(
            month=TruncMonth(Cast("Id10023", output_field=DateField()))
        )
        .filter(causes__isnull=False)
        .values("month")
        .annotate(count=Count("pk"))
        .order_by("month")
    )

    place_of_death = (
        user_vas_filtered.filter(causes__isnull=False)
        .values(place=F("Id10058"))
        .annotate(count=Count("pk"))
        .order_by("-count")
    )

    geographic_province_sums = (
        user_vas_filtered.annotate(
            province_name=Subquery(
                Location.objects.values("name").filter(
                    Q(path=Substr(OuterRef("location__path"), 1, 8)), Q(depth=2)
                )[:1]
            )
        )
        .filter(causes__isnull=False)
        .select_related("location")
        .values("province_name")
        .annotate(count=Count("pk"))
    )

    geographic_district_sums = (
        user_vas_filtered.annotate(
            district_name=Subquery(
                Location.objects.values("name").filter(
                    Q(path=Substr(OuterRef("location__path"), 1, 12)), Q(depth=3)
                )[:1]
            )
        )
        .filter(causes__isnull=False)
        .select_related("location")
        .values("district_name")
        .annotate(count=Count("pk"))
    )

    data = {
        "COD_grouping": COD_sums,
        "COD_trend": COD_trend,
        "place_of_death": place_of_death,
        "demographics": demographics,
        "geographic_province_sums": geographic_province_sums,
        "geographic_district_sums": geographic_district_sums,
        "uncoded_vas": uncoded_vas,
        "update_stats": update_stats,
        "all_causes_list": load_cod_groupings(cause_of_death=cause_of_death)[
            "dropdown_options"
        ],
    }

    return data
