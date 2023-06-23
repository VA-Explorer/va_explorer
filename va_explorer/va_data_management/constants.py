from django.utils.translation import gettext_lazy as _

"""
Please refer to WHOVA Instrument 'choices' tab for keys/values source

Note: Some options are intentionally split to prevent having to translate the
      same word multiple times.
"""

_age_group = [
    ("neonate", _("Neonate")),
    ("child", _("Child")),
    ("adult", _("Adult")),
]

_no = [("no", _("No"))]
_yes_no = [("yes", _("Yes")), *_no]
_dk = [("DK", _("Doesn't know"))]
_ref = [("ref", _("Refused to answer"))]
_other = [("other", _("Other"))]
_dk_ref = _dk + _ref

_yes_no_ref = _yes_no + _ref
_yes_no_dk_ref = _yes_no + _dk_ref

_high_low_very = [
    ("high", _("High")),
    ("low", _("Low")),
    ("veryl", _("Very low")),
]

YEARS = [("years", _("Years"))]
MONTHS = [("months", _("Months"))]
DAYS = [("days", _("Days"))]
HOURS = [("hours", _("Hours"))]
MINUTES = [("minutes", _("Minutes"))]

M_H_D_DK = MINUTES + HOURS + DAYS + _dk_ref
D_M_DK_REF = DAYS + MONTHS + _dk_ref
H_D_DK_REF = HOURS + DAYS + _dk_ref
H_D_M_DK = HOURS + DAYS + MONTHS + _dk_ref
M_H_M_DK = MINUTES + HOURS + MONTHS + _dk

_select_2 = [
    ("female", _("Female")),
    ("male", _("Male")),
    ("undetermined", _("Ambiguous / Intersex")),
]

_select_18 = [
    *_dk_ref,
    ("hospital", _("Hospital")),
    ("other_health_facility", _("Other health facility")),
    ("home", _("Home")),
    ("on_route_to_hospital_or_facility", _("On route to hospital or facility")),
    *_other,
]

_select_19 = [
    *_dk_ref,
    ("single", _("Single")),
    ("married", _("Married")),
    ("partner", _("Partner")),
    ("divorced", _("Divorced")),
    ("widowed", _("Widowed")),
    ("too_young_to_be_married", _("Too young to be married")),
]

_select_23 = [
    *_dk_ref,
    ("no_formal_education", _("No formal education")),
    ("primary_school", _("Primary school")),
    ("secondary_school", _("Secondary school")),
    ("higher_than_secondary_school", _("Higher than secondary school")),
]

_select_25 = [
    *_dk_ref,
    ("mainly_unemployed", _("Mainly unemployed")),
    ("mainly_employed", _("Mainly employed")),
    ("home-maker", _("Home-maker")),
    ("pensioner", _("Pensioner")),
    ("student", _("Student")),
    *_other,
]

_select_32 = [
    *_ref,
    ("parent", _("Parent")),
    ("child", _("Child")),
    ("family_member", _("Other family member")),
    ("friend", _("Friend")),
    ("spouse", _("Spouse")),
    ("health_worker", _("Health worker")),
    ("public_official", _("Public official")),
    ("another_relationship", _("Another relationship")),
]

_select_58 = [("wet", _("Wet")), ("dry", _("Dry")), *_dk]

_select_63 = [
    ("mild", _("Mild")),
    ("moderate", _("Moderate")),
    ("severe", _("Severe")),
    *_dk_ref,
]

_select_64 = [
    ("continuous", _("Continuous")),
    ("on_and_off", _("On and off")),
    *_dk_ref,
]

_select_100 = [
    ("upper_abdomen", _("Upper abdomen")),
    ("lower_abdomen", _("Lower abdomen")),
    ("upper_lower_abdomen", _("Upper and lower abdomen")),
    *_dk_ref,
]

_select_103 = [("rapidly", _("Rapidly")), ("slowly", _("Slowly")), *_dk_ref]

_select_135 = [
    ("face", _("Face")),
    ("trunk", _("Trunk or abdomen")),
    ("extremities", _("Extremities")),
    ("everywhere", _("Everywhere")),
    *_dk_ref,
]

_select_161 = [
    ("right_side", _("Right side")),
    ("left_side", _("Left side")),
    ("lower_part_of_body", _("Lower part of body")),
    ("upper_part_of_body", _("Upper part of body")),
    ("one_leg_only", _("One leg only")),
    ("one_arm_only", _("One arm only")),
    ("whole_body", _("Whole body")),
    *_other,
    *_dk_ref,
]

_select_164 = [
    ("solids", _("Solids")),
    ("liquids", _("Liquids")),
    ("both", _("Both")),
    *_dk_ref,
]

_select_208 = _select_18

_select_219 = [
    ("first", _("First")),
    ("second_or_later", _("Second or later")),
    *_dk_ref,
]

_select_223 = _select_18

_ped = [("pedestrian", _("Pedestrian"))]
_select_292 = (
    _dk_ref
    + _ped
    + [
        ("in_car_or_light_vehicle", _("Driver or passenger in car or light vehicle")),
        ("in_bus_or_heavy_vehicle", _("Driver or passenger in bus or heavy vehicle")),
        ("on_a_motorcycle", _("Driver or passenger on a motorcycle")),
        ("on_a_pedal_cycle", _("Driver or passenger on a pedal cycle")),
    ]
    + _other
)

_select_293 = (
    _dk_ref
    + _ped
    + [
        ("stationary_object", _("Stationary object")),
        ("car_or_light_vehicle", _("Car or light vehicle")),
        ("bus_or_heavy_vehicle", _("Bus or heavy vehicle")),
        ("motorcycle", _("Motorcycle")),
        ("pedal_cycle", _("Pedal cycle")),
    ]
    + _other
)

_select_299 = [
    *_dk_ref,
    ("dog", _("Dog")),
    ("snake", _("Snake")),
    ("insect_or_scorpion", _("Insect or scorpion")),
    *_other,
]

_select_306 = [
    *_dk_ref,
    ("cigarettes", _("Cigarettes")),
    ("pipe", _("Pipe")),
    ("chewing_tobacco", _("Chewing tobacco")),
    ("local_form_of_tobacco", _("Local form of tobacco")),
    *_other,
]

_select_322 = [
    ("traditional_healer", _("Traditional healer")),
    ("homeopath", _("Homeopath")),
    ("religious_leader", _("Religious leader")),
    ("government_hospital", _("Government hospital")),
    ("govment_health_center_or_clinic", _("Government health center or clinic")),
    ("private_hospital", _("Private hospital")),
    (
        "community_based_pract_system",
        _("Community-based practitioner associated with health system"),
    ),
    ("trained_birth_attendant", _("Trained birth attendant")),
    ("private_physician", _("Private physician")),
    ("relative_friend", _("Relative, friend (outside household)")),
    ("pharmacy", _("Pharmacy")),
    *_dk_ref,
]

_select_500 = [
    ("citizen_at_birth", _("Citizen at birth")),
    ("naturalized_citizen", _("Naturalized citizen")),
    ("foreign_national", _("Foreign national")),
    *_dk_ref,
]

_select_501 = [
    ("stridor", _("Stridor")),
    ("grunting", _("Grunting")),
    ("wheezing", _("Wheezing")),
    *_no,
    *_dk_ref,
]

_none = [("None", _("None of the above words were mentioned"))]
_select_510 = [
    ("Chronic_kidney_disease", _("Chronic kidney disease")),
    ("Dialysis", _("Dialysis")),
    ("Fever", _("Fever")),
    ("Heart_attack", _("Heart attack")),
    ("Heart_problem", _("Heart problem")),
    ("Jaundice", _("Jaundice")),
    ("Liver_failure", _("Liver failure")),
    ("Malaria", _("Malaria")),
    ("Pneumonia", _("Pneumonia")),
    ("Renal_kidney_failure", _("Renal (kidney) failure")),
    ("Suicide", _("Suicide")),
    *_none,
    *_dk,
]

_select_511 = [
    ("asphyxia", _("Asphyxia")),
    ("incubator", _("Incubator")),
    ("lung_problem", _("Lung problem")),
    ("pneumonia", _("Pneumonia")),
    ("preterm_delivery", _("Preterm delivery")),
    ("respiratory_distress", _("Respiratory distress")),
    *_none,
    *_dk,
]

_select_512 = [
    ("abdomen", _("Abdomen")),
    ("cancer", _("Cancer")),
    ("dehydration", _("Dehydration")),
    ("dengue", _("Dengue fever")),
    ("diarrhea", _("Diarrhoea")),
    ("fever", _("Fever")),
    ("heart_problem", _("Heart problems")),
    ("jaundice", _("Jaundice (yellow skin or eyes)")),
    ("pneumonia", _("Pneumonia")),
    ("rash", _("Rash")),
    *_none,
    *_dk,
]

_select_520 = [
    ("green_or_brown", _("Green or brown")),
    ("clear", _("Clear (normal)")),
    *_other,
    *_dk_ref,
]

_select_530 = [
    *_dk_ref,
    ("Doctor", _("Doctor")),
    ("Midwife", _("Midwife")),
    ("Nurse", _("Nurse")),
    ("Relative", _("Relative")),
    ("Self_mother", _("Self (the mother)")),
    ("Traditional_birth_attendant", _("Traditional birth attendant")),
    *_other,
]

_select_531 = [
    ("positive", _("Positive")),
    ("negative", _("Negative")),
    ("unclear", _("Unclear")),
    *_dk_ref,
]

_select_vaccines = [
    ("BCG", _("BCG")),
    ("DPT_123", _("DPT 1,2,3")),
    ("HepB", _("Hep B")),
    ("Hib", _("Hib")),
    ("Measles", _("Measles")),
    ("Meningitis", _("Meningitis")),
    ("Penta_123", _("Penta 1,2,3")),
    ("Pneumo", _("Pneumo")),
    ("Polio_123", _("Polio 1,2,3")),
    ("Rota", _("Rota")),
    ("no", _("No Vaccines")),
    *_dk,
]


_radio_choices = {
    "Id10002": _high_low_very,
    "Id10003": _high_low_very,
    "Id10004": _select_58,
    "Id10009": _yes_no_dk_ref,
    "Id10013": _yes_no,
    "Id10019": _select_2,
    "Id10020": _yes_no_ref,
    "Id10022": _yes_no_ref,
    "age_group": _age_group,
    "Id10487": _yes_no_dk_ref,
    "Id10488": _yes_no_dk_ref,
    "Id10051": _yes_no,
    "Id10052": _select_500,
    "Id10060_check": _yes_no,
    "Id10064": _yes_no_dk_ref,
    "Id10069": _yes_no,
    "Id10069_a": _yes_no,
    "Id10071_check": _yes_no,
    "Id10104": _yes_no_dk_ref,
    "Id10105": _yes_no_dk_ref,
    "Id10107": _yes_no_dk_ref,
    "Id10109": _yes_no_dk_ref,
    "Id10110": _yes_no_dk_ref,
    "Id10111": _yes_no_dk_ref,
    "Id10112": _yes_no_dk_ref,
    "Id10113": _yes_no_dk_ref,
    "Id10114": _yes_no_dk_ref,
    "Id10115": _yes_no_dk_ref,
    "Id10116": _yes_no_dk_ref,
    "Id10077": _yes_no_dk_ref,
    "Id10079": _yes_no_dk_ref,
    "Id10082": _yes_no_dk_ref,
    "Id10083": _yes_no_dk_ref,
    "Id10084": _yes_no_dk_ref,
    "Id10085": _yes_no_dk_ref,
    "Id10086": _yes_no_dk_ref,
    "Id10087": _yes_no_dk_ref,
    "Id10089": _yes_no_dk_ref,
    "Id10090": _yes_no_dk_ref,
    "Id10091": _yes_no_dk_ref,
    "Id10092": _yes_no_dk_ref,
    "Id10093": _yes_no_dk_ref,
    "Id10094": _yes_no_dk_ref,
    "Id10095": _yes_no_dk_ref,
    "Id10096": _yes_no_dk_ref,
    "Id10097": _yes_no_dk_ref,
    "Id10098": _yes_no_dk_ref,
    "Id10099": _yes_no_dk_ref,
    "Id10100": _yes_no_dk_ref,
    "Id10408": _yes_no_dk_ref,
    "Id10123": _yes_no_dk_ref,
    "Id10125": _yes_no_dk_ref,
    "Id10126": _yes_no_dk_ref,
    "Id10127": _yes_no_dk_ref,
    "Id10128": _yes_no_dk_ref,
    "Id10129": _yes_no_dk_ref,
    "Id10130": _yes_no_dk_ref,
    "Id10131": _yes_no_dk_ref,
    "Id10132": _yes_no_dk_ref,
    "Id10133": _yes_no_dk_ref,
    "Id10134": _yes_no_dk_ref,
    "Id10135": _yes_no_dk_ref,
    "Id10136": _yes_no_dk_ref,
    "Id10137": _yes_no_dk_ref,
    "Id10138": _yes_no_dk_ref,
    "Id10139": _yes_no_dk_ref,
    "Id10140": _yes_no_dk_ref,
    "Id10141": _yes_no_dk_ref,
    "Id10142": _yes_no_dk_ref,
    "Id10143": _yes_no_dk_ref,
    "Id10144": _yes_no_dk_ref,
    "Id10482": _yes_no_dk_ref,
    "Id10483": _yes_no_dk_ref,
    "Id10484": _select_531,
    "Id10147": _yes_no_dk_ref,
    "Id10149": _yes_no_dk_ref,
    "Id10150": _select_63,
    "Id10151": _select_64,
    "Id10152": _yes_no_dk_ref,
    "Id10153": _yes_no_dk_ref,
    "Id10155": _yes_no_dk_ref,
    "Id10156": _yes_no_dk_ref,
    "Id10157": _yes_no_dk_ref,
    "Id10158": _yes_no_dk_ref,
    "Id10159": _yes_no_dk_ref,
    "Id10166": _yes_no_dk_ref,
    "Id10168": _yes_no_dk_ref,
    "Id10170": _yes_no_dk_ref,
    "Id10171": _yes_no_dk_ref,
    "Id10172": _yes_no_dk_ref,
    "Id10173_a": _yes_no_dk_ref,
    "Id10174": _yes_no_dk_ref,
    "Id10175": _yes_no_dk_ref,
    "Id10181": _yes_no_dk_ref,
    "Id10185": _yes_no_dk_ref,
    "Id10186": _yes_no_dk_ref,
    "Id10187": _yes_no_dk_ref,
    "Id10188": _yes_no_dk_ref,
    "Id10189": _yes_no_dk_ref,
    "Id10191": _yes_no_dk_ref,
    "Id10192": _yes_no_dk_ref,
    "Id10193": _yes_no_dk_ref,
    "Id10194": _yes_no_dk_ref,
    "Id10195": _yes_no_dk_ref,
    "Id10199": _select_100,
    "Id10200": _yes_no_dk_ref,
    "Id10203": _select_103,
    "Id10204": _yes_no_dk_ref,
    "Id10207": _yes_no_dk_ref,
    "Id10208": _yes_no_dk_ref,
    "Id10210": _yes_no_dk_ref,
    "Id10212": _yes_no_dk_ref,
    "Id10214": _yes_no_dk_ref,
    "Id10215": _yes_no_dk_ref,
    "Id10217": _yes_no_dk_ref,
    "Id10218": _yes_no_dk_ref,
    "Id10219": _yes_no_dk_ref,
    "Id10220": _yes_no_dk_ref,
    "Id10222": _yes_no_dk_ref,
    "Id10223": _yes_no_dk_ref,
    "Id10225": _yes_no_dk_ref,
    "Id10226": _yes_no_dk_ref,
    "Id10224": _yes_no_dk_ref,
    "Id10227": _yes_no_dk_ref,
    "Id10228": _yes_no_dk_ref,
    "Id10229": _yes_no_dk_ref,
    "Id10230": _yes_no_dk_ref,
    "Id10231": _yes_no_dk_ref,
    "Id10233": _yes_no_dk_ref,
    "Id10236": _yes_no_dk_ref,
    "Id10237": _yes_no_dk_ref,
    "Id10238": _yes_no_dk_ref,
    "Id10239": _yes_no_dk_ref,
    "Id10240": _yes_no_dk_ref,
    "Id10241": _yes_no_dk_ref,
    "Id10242": _yes_no_dk_ref,
    "Id10243": _yes_no_dk_ref,
    "Id10244": _yes_no_dk_ref,
    "Id10245": _yes_no_dk_ref,
    "Id10246": _yes_no_dk_ref,
    "Id10247": _yes_no_dk_ref,
    "Id10249": _yes_no_dk_ref,
    "Id10251": _yes_no_dk_ref,
    "Id10252": _yes_no_dk_ref,
    "Id10253": _yes_no_dk_ref,
    "Id10254": _yes_no_dk_ref,
    "Id10255": _yes_no_dk_ref,
    "Id10256": _yes_no_dk_ref,
    "Id10257": _yes_no_dk_ref,
    "Id10258": _yes_no_dk_ref,
    "Id10259": _yes_no_dk_ref,
    "Id10261": _yes_no_dk_ref,
    "Id10263": _select_164,
    "Id10264": _yes_no_dk_ref,
    "Id10265": _yes_no_dk_ref,
    "Id10267": _yes_no_dk_ref,
    "Id10268": _yes_no_dk_ref,
    "Id10269": _yes_no_dk_ref,
    "Id10270": _yes_no_dk_ref,
    "Id10271": _yes_no_dk_ref,
    "Id10272": _yes_no_dk_ref,
    "Id10273": _yes_no_dk_ref,
    "Id10275": _yes_no_dk_ref,
    "Id10276": _yes_no_dk_ref,
    "Id10277": _yes_no_dk_ref,
    "Id10278": _yes_no_dk_ref,
    "Id10279": _yes_no_dk_ref,
    "Id10281": _yes_no_dk_ref,
    "Id10282": _yes_no_dk_ref,
    "Id10283": _yes_no_dk_ref,
    "Id10284": _yes_no_dk_ref,
    "Id10286": _yes_no_dk_ref,
    "Id10287": _yes_no_dk_ref,
    "Id10288": _yes_no_dk_ref,
    "Id10289": _yes_no_dk_ref,
    "Id10290": _yes_no_dk_ref,
    "Id10485": _yes_no_dk_ref,
    "Id10486": _yes_no_dk_ref,
    "Id10294": _yes_no_dk_ref,
    "Id10295": _yes_no_dk_ref,
    "Id10296": _yes_no_dk_ref,
    "Id10297": _yes_no_dk_ref,
    "Id10298": _yes_no_dk_ref,
    "Id10301": _yes_no_dk_ref,
    "Id10299": _yes_no_dk_ref,
    "Id10302": _yes_no_dk_ref,
    "Id10300": _yes_no_dk_ref,
    "Id10304": _yes_no_dk_ref,
    "Id10305": _yes_no_dk_ref,
    "Id10306": _yes_no_dk_ref,
    "Id10307": _yes_no_dk_ref,
    "Id10308": _yes_no_dk_ref,
    "Id10310": _yes_no_dk_ref,
    "Id10312": _yes_no_dk_ref,
    "Id10313": _yes_no_dk_ref,
    "Id10314": _yes_no_dk_ref,
    "Id10315_a": _yes_no_dk_ref,
    "Id10316": _yes_no_dk_ref,
    "Id10317": _yes_no_dk_ref,
    "Id10318": _yes_no_dk_ref,
    "Id10320": _yes_no_dk_ref,
    "Id10321": _yes_no_dk_ref,
    "Id10322": _yes_no_dk_ref,
    "Id10323": _yes_no_dk_ref,
    "Id10324": _yes_no_dk_ref,
    "Id10325": _yes_no_dk_ref,
    "Id10326": _yes_no_dk_ref,
    "Id10327": _yes_no_dk_ref,
    "Id10328": _yes_no_dk_ref,
    "Id10329": _yes_no_dk_ref,
    "Id10330": _yes_no_dk_ref,
    "Id10331": _yes_no_dk_ref,
    "Id10333": _yes_no_dk_ref,
    "Id10334": _yes_no_dk_ref,
    "Id10335": _yes_no_dk_ref,
    "Id10336": _yes_no_dk_ref,
    "Id10338": _yes_no_dk_ref,
    "Id10342": _yes_no_dk_ref,
    "Id10343": _yes_no_dk_ref,
    "Id10344": _yes_no_dk_ref,
    "Id10347": _yes_no_dk_ref,
    "Id10340": _yes_no_dk_ref,
    "Id10354": _yes_no_dk_ref,
    "Id10355": _select_219,
    "Id10356": _yes_no_dk_ref,
    "Id10361": _yes_no_dk_ref,
    "Id10362": _yes_no_dk_ref,
    "Id10363": _yes_no_dk_ref,
    "Id10364": _yes_no_dk_ref,
    "Id10365": _yes_no_dk_ref,
    "Id10368": _yes_no_dk_ref,
    "Id10369": _yes_no_dk_ref,
    "Id10370": _yes_no_dk_ref,
    "Id10371": _yes_no_dk_ref,
    "Id10372": _yes_no_dk_ref,
    "Id10373": _yes_no_dk_ref,
    "Id10376": _yes_no_dk_ref,
    "Id10377": _yes_no_dk_ref,
    "Id10383": _yes_no_dk_ref,
    "Id10384": _yes_no_dk_ref,
    "Id10385": _select_520,
    "Id10387": _yes_no_dk_ref,
    "Id10388": _yes_no_dk_ref,
    "Id10389": _yes_no_dk_ref,
    "Id10391": _yes_no_dk_ref,
    "Id10393": _yes_no_dk_ref,
    "Id10395": _yes_no_dk_ref,
    "Id10396": _yes_no_dk_ref,
    "Id10397": _yes_no_dk_ref,
    "Id10398": _yes_no_dk_ref,
    "Id10399": _yes_no_dk_ref,
    "Id10400": _yes_no_dk_ref,
    "Id10401": _yes_no_dk_ref,
    "Id10402": _yes_no_dk_ref,
    "Id10403": _yes_no_dk_ref,
    "Id10404": _yes_no_dk_ref,
    "Id10405": _yes_no_dk_ref,
    "Id10406": _yes_no_dk_ref,
    "Id10411": _yes_no_dk_ref,
    "Id10412": _yes_no_dk_ref,
    "Id10413": _yes_no_dk_ref,
    "Id10418": _yes_no_dk_ref,
    "Id10419": _yes_no_dk_ref,
    "Id10420": _yes_no_dk_ref,
    "Id10421": _yes_no_dk_ref,
    "Id10422": _yes_no_dk_ref,
    "Id10423": _yes_no_dk_ref,
    "Id10424": _yes_no_dk_ref,
    "Id10425": _yes_no_dk_ref,
    "Id10426": _yes_no_dk_ref,
    "Id10427": _yes_no_dk_ref,
    "Id10428": _yes_no_dk_ref,
    "Id10429": _yes_no_dk_ref,
    "Id10430": _yes_no_dk_ref,
    "Id10432": _yes_no_dk_ref,
    "Id10435": _yes_no_dk_ref,
    "Id10437": _yes_no_dk_ref,
    "Id10438": _yes_no_dk_ref,
    "Id10439_check": _yes_no,
    "Id10440_check": _yes_no,
    "Id10441_check": _yes_no,
    "Id10445": _yes_no_dk_ref,
    "Id10446": _yes_no_dk_ref,
    "Id10450": _yes_no_dk_ref,
    "Id10451": _yes_no_dk_ref,
    "Id10452": _yes_no_dk_ref,
    "Id10453": _yes_no_dk_ref,
    "Id10454": _yes_no_dk_ref,
    "Id10455": _yes_no_dk_ref,
    "Id10456": _yes_no_dk_ref,
    "Id10457": _yes_no_dk_ref,
    "Id10458": _yes_no_dk_ref,
    "Id10459": _yes_no_dk_ref,
    "Id10462": _yes_no_dk_ref,
    "Id10463": _yes_no_dk_ref,
}

_checkbox_choices = {
    "Id10173_nc": _select_501,
    "Id10235": _select_135,
    "Id10260": _select_161,
    "Id10431": _select_vaccines,
    "Id10433": _select_322,
    "Id10477": _select_510,
    "Id10478": _select_511,
    "Id10479": _select_512,
}

# Generally >5 choices assigned here instead of radio buttons (if not checkbox)
_dropdown_choices = {
    "Id10008": _select_32,
    "Id10058": _select_18,
    "Id10059": _select_19,
    "Id10063": _select_23,
    "Id10065": _select_25,
    "Id10080": _select_292,
    "Id10081": _select_293,
    "Id10088": _select_299,
    "Id10337": _select_208,
    "Id10339": _select_530,
    "Id10360": _select_223,
    "Id10414": _select_306,
}

_text_fields = [
    "deviceid",
    "phonenumber",
    "simserial",
    "username",
    "bid",
    "province",  # TODO: convert to dynamic dropdown
    "area",  # TODO: convert to dynamic dropdown
    "hospital" "Id10007",  # TODO: convert to dynamic dropdown
    "Id10010",
    "Id10010c",
    "Id10017",
    "Id10018",
    "Id10053",
    # "Id10054",        # uses a textarea in forms.py
    # "Id10055",        # uses a textarea in forms.py
    "Id10057",
    "Id10061",
    "Id10062",
    "Id10066",
    "Id10070",
    "Id10072",
    "Id10073",
    # "Id10434",        # uses a textarea in forms.py
    # "Id10436",        # uses a textarea in forms.py
    # "Id10444",        # uses a textarea in forms.py
    "Id10464",
    "Id10465",
    "Id10466",
    "Id10467",
    "Id10468",
    "Id10469",
    "Id10470",
    "Id10471",
    "Id10472",
    "Id10473",
    # "Id10476",        # uses a textarea in forms.py
    # "comment",        # uses a textarea in forms.py
]

_number_fields = [
    "Id10010a",
    "age_neonate_days",
    "age_child_days",
    "age_child_months",
    "age_child_years",
    "age_adult",
    "Id10024",
    "Id10106",
    "Id10108",
    "Id10351",
    "Id10120_0",
    "Id10121",
    "Id10122",
    "Id10120_1",
    "Id10148_a",
    "Id10148_b",
    "Id10148_c",
    "Id10154_a",
    "Id10154_b",
    "Id10161_0",
    "Id10161_1",
    "Id10162",
    "Id10163",
    "Id10167_a",
    "Id10167_b",
    "Id10167_c",
    "Id10169_a",
    "Id10169_b",
    "Id10169_c",
    "Id10176",
    "Id10178",
    "Id10179",
    "Id10179_1",
    "Id10182_a",
    "Id10182_b",
    "Id10183",
    "Id10184_a",
    "Id10184_b",
    "Id10184_c",
    "Id10190_a",
    "Id10190_b",
    "Id10196",
    "Id10197_a",
    "Id10198",
    "Id10201_a",
    "Id10202",
    "Id10205_a",
    "Id10206",
    "Id10209_a",
    "Id10209_b",
    "Id10211_a",
    "Id10211_b",
    "Id10213_a",
    "Id10213_b",
    "Id10216_a",
    "Id10216_b",
    "Id10221",
    "Id10232_a",
    "Id10232_b",
    "Id10234",
    "Id10248_a",
    "Id10248_b",
    "Id10250_a",
    "Id10250_b",
    "Id10262_a",
    "Id10262_b",
    "Id10266_a",
    "Id10266_b",
    "Id10274_a",
    "Id10274_b",
    "Id10274_c",
    "Id10285",
    "Id10303",
    "Id10309",
    "Id10319",
    "Id10332",
    "Id10352_a",
    "Id10352_b",
    "Id10358",
    "Id10359",
    "Id10359_a",
    "Id10367",
    "Id10394",
    "Id10379",
    "Id10380",
    "Id10382",
    "Id10392",
    "Id10415",
    "Id10416",
    "Id10442",
    "Id10443",
]

_date_fields = [
    "submissiondate",
    "Id10021",
    "Id10023_a",
    "Id10023_b",
    "Id10060",
    "Id10071",
    "Id10439",
    "Id10440",
    "Id10441",
]

_time_fields = [
    "Id10011",
]

_datetime_fields = [
    "Id10012",
    "Id10481",
]

_display_fields = [
    "Id10023",
    "ageInDays",
    "ageInDays2",
    "ageInYears",
    "ageInYearsRemain",
    "ageInMonths",
    "ageInMonthsRemain",
    "isNeonatal1",
    "isChild1",
    "isAdult1",
    "ageInMonthsByYear",
    "ageInYears2",
    "isNeonatal2",
    "isChild2",
    "isAdult2",
    "isNeonatal",
    "isChild",
    "isAdult",
    "ageInDaysNeonate",
    "Id10120",
    "Id10148",
    "Id10154",
    "Id10161",
    "Id10167",
    "Id10169",
    "Id10173",
    "Id10182",
    "Id10197",
    "Id10201",
    "Id10205",
    "Id10209",
    "Id10211",
    "Id10213",
    "Id10216",
    "Id10232",
    "Id10248",
    "Id10250",
    "Id10262",
    "Id10266",
    "Id10274",
    "Id10315",
    "Id10352",
    "Id10366",
]

HIDDEN_FIELDS = (
    "id",
    "location",
    "instanceid",
    "instanceName",
    "deleted_at",
    "unique_va_identifier",
    "duplicate",
    "bid2",
    "bid_check",
    "displayAgeNeonate",
    "displayAgeChild",
    "displayAgeAdult",
    "Id10008_check",
    "id10173_check",
    "id10235_check",
    "id10260_check",
    "id10260_check2",
    "Id10310_check",
    "id1036X_check",
    "id10389_check",
    "id10414_check",
    "id10431_check",
    "id10433_check",
    "id10477_check",
    "id10478_check",
    "id10479_check",
    "geopoint",  # GPS data stored on VAs sent from ODK?
)

FORM_FIELDS = {
    "text": _text_fields,
    "radio": _radio_choices,
    "checkbox": _checkbox_choices,
    "dropdown": _dropdown_choices,
    "number": _number_fields,
    "date": _date_fields,
    "time": _time_fields,
    "datetime": _datetime_fields,
    "display": _display_fields,  # corresponds to calculate in WHO instrument
}

REDACTED_STRING = "** redacted **"

PII_FIELDS = [
    "Id10007",
    "Id10017",
    "Id10018",
    "Id10061",
    "Id10062",
    "Id10070",
    "Id10073",
]
