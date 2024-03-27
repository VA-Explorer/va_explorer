# flake8: noqa: N815 - We want the model fields to exactly reflect the VA instrument's fields
import contextlib
import hashlib

from django.conf import settings
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.db.models import Count, JSONField
from simple_history.models import HistoricalRecords
from treebeard.mp_tree import MP_Node

from va_explorer.models import SoftDeletionModel

from .constants import (
    _select_135,
    _select_161,
    _select_322,
    _select_501,
    _select_510,
    _select_511,
    _select_512,
    _select_vaccines,
)
from .utils.multi_select import MultiSelectField


class Location(MP_Node):
    # Locations are set up as a tree structure, allowing a regions and sub-regions along with the
    # ability to constrain access control by region; we use django-treebeard's materialized path
    # implementation for efficiency of tree operations
    name = models.TextField()
    location_type = models.TextField()
    is_active = models.BooleanField(default=False)
    key = models.TextField(blank=True)
    path_string = models.TextField(unique=True, null=True)
    node_order_by = ["name"]

    # A user can have their access scoped by one or more locations
    # users = models.ManyToManyField(get_user_model(), related_name='locations')

    # Automatically set timestamps
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def get_descendant_ids(self):
        return [descendant.id for descendant in self.get_descendants()]

    def parent_id(self):
        return self.get_parent().id


class VerbalAutopsy(SoftDeletionModel):
    class Meta:
        permissions = (("bulk_delete", "Can bulk delete"),)
        indexes = [
            models.Index(fields=["unique_va_identifier"]),
            models.Index(fields=["Id10023"], name="death_date_filter_idx"),
        ]

    # Each VerbalAutopsy is associated with a facility, which is the leaf node location
    location = models.ForeignKey(
        Location, related_name="verbalautopsies", on_delete=models.CASCADE, null=True
    )

    # The VA fields collected as part of the WHO VA form or local versions
    # TODO: Need an approach that supports different variants in different countries
    deviceid = models.TextField("Device ID", blank=True)
    instanceid = models.TextField("Instance ID", blank=True, editable=False)
    instancename = models.TextField("Instance Name", blank=True, editable=False)
    phonenumber = models.TextField("Phone Number", blank=True)
    simserial = models.TextField("SIM Serial", blank=True)
    username = models.TextField("Username", blank=True)
    bid = models.TextField("BID", blank=True)
    bid2 = models.TextField("BID2", blank=True)
    bid_check = models.TextField("BID Check", blank=True)
    bid_image = models.TextField("BID Image", blank=True)
    province = models.TextField("Province", blank=True)
    area = models.TextField("Area", blank=True)
    hospital = models.TextField("Hospital", blank=True)
    submissiondate = models.TextField("Submission Date", blank=True)
    Id10002 = models.TextField(
        "Is this a region of high HIV/AIDS mortality?", blank=True
    )
    Id10003 = models.TextField(
        "Is this a region of high malaria mortality?", blank=True
    )
    Id10004 = models.TextField("During which season did (s)he die?", blank=True)
    Id10007 = models.TextField("What is the name of VA respondent?", blank=True)
    Id10008 = models.TextField(
        "What is your/the respondent's relationship to the deceased?", blank=True
    )
    Id10009 = models.TextField(
        "Did you/the respondent live with the deceased in the period leading to her/his death?",
        blank=True,
    )
    Id10010 = models.TextField("Name of VA interviewer", blank=True)
    Id10012 = models.TextField("Date of interview", blank=True)
    Id10013 = models.TextField("Did the respondent give consent?", blank=True)
    Id10011 = models.TextField("Time at start of interview", blank=True)
    Id10017 = models.TextField(
        "What was the first or given name(s) of the deceased?", blank=True
    )
    Id10018 = models.TextField(
        "What was the surname (or family name) of the deceased?", blank=True
    )
    Id10019 = models.TextField("What was the sex of the deceased?", blank=True)
    Id10020 = models.TextField("Is the date of birth known?", blank=True)
    Id10021 = models.TextField("When was the deceased born?", blank=True)
    Id10022 = models.TextField("Is the date of death known?", blank=True)
    Id10023_a = models.TextField("When did (s)he die?", blank=True)
    Id10023_b = models.TextField("When did (s)he die?", blank=True)
    Id10023 = models.TextField("Calculated Field: When did (s)he die?", blank=True)
    Id10024 = models.TextField("Please indicate the year of death.", blank=True)
    ageInDays = models.TextField("Calculated Field: ageInDays", blank=True)
    ageInDays2 = models.TextField("Calculated Field: ageInDays2", blank=True)
    ageInYears = models.TextField("Calculated Field: ageInYears", blank=True)
    ageInYearsRemain = models.TextField(
        "Calculated Field: ageInYearsRemain", blank=True
    )
    ageInMonths = models.TextField("Calculated Field: ageInMonths", blank=True)
    ageInMonthsRemain = models.TextField(
        "Calculated Field: ageInMonthsRemain", blank=True
    )
    isNeonatal1 = models.TextField("Calculated Field: isNeonatal1", blank=True)
    isChild1 = models.TextField("Calculated Field: isChild1", blank=True)
    isAdult1 = models.TextField("Calculated Field: isAdult1", blank=True)
    displayAgeNeonate = models.TextField(
        "NEONATE was ${ageInDays} days old.", blank=True
    )
    displayAgeChild = models.TextField(
        "CHILD was ${ageInYears} years ${ageInMonths} months and ${ageInMonthsRemain} days old.",
        blank=True,
    )
    displayAgeAdult = models.TextField("ADULT was ${ageInYears} years old.", blank=True)
    age_group = models.TextField(
        "What age group corresponds to the deceased?", blank=True
    )
    age_neonate_days = models.TextField(
        "How many days old was the baby? [Enter neonate's age in days:]", blank=True
    )
    age_child_unit = models.TextField(
        "How old was the child? [Enter child's age in:]", blank=True
    )
    age_child_days = models.TextField("Enter child's age in days:", blank=True)
    age_child_months = models.TextField("Enter child's age in months:", blank=True)
    age_child_years = models.TextField("Enter child's age in years:", blank=True)
    age_adult = models.TextField("Enter adult's age in years:", blank=True)
    ageInMonthsByYear = models.TextField(
        "Calculated Field: ageInMonthsByYear", blank=True
    )
    ageInYears2 = models.TextField("Calculated Field: ageInYears2", blank=True)
    isNeonatal2 = models.TextField("Calculated Field: isNeonatal2", blank=True)
    isChild2 = models.TextField("Calculated Field: isChild2", blank=True)
    isAdult2 = models.TextField("Calculated Field: isAdult2", blank=True)
    isNeonatal = models.TextField("Calculated Field: isNeonatal", blank=True)
    isChild = models.TextField("Calculated Field: isChild", blank=True)
    isAdult = models.TextField("Calculated Field: isAdult", blank=True)
    ageInDaysNeonate = models.TextField(
        "Calculated Field: ageInDaysNeonate", blank=True
    )
    Id10008_check = models.TextField(
        "It is not possible to select that the respondent is the child of the \
        deceased and enter that the deceased is a neonate or child. Please go \
        back and correct the selection.",
        blank=True,
    )
    Id10058 = models.TextField("Where did the deceased die?", blank=True)
    Id10487 = models.TextField(
        "In the two weeks before death, did (s)he live with, visit, or care for someone who had any COVID-19 symptoms or a positive COVID-19 test?",
        blank=True,
    )
    Id10488 = models.TextField(
        "In the two weeks before death, did (s)he travel to an area where COVID-19 is known to be present?",
        blank=True,
    )
    Id10051 = models.TextField(
        "Is there a need to collect additional demographic data on the deceased?",
        blank=True,
    )
    Id10052 = models.TextField("What was her/his citizenship/nationality?", blank=True)
    Id10053 = models.TextField("What was her/his ethnicity?", blank=True)
    Id10054 = models.TextField("What was her/his place of birth?", blank=True)
    Id10055 = models.TextField(
        "What was her/his place of usual residence? (the place where the person \
        lived most of the year)",
        blank=True,
    )
    Id10057 = models.TextField(
        "Where did the death occur? (specify country, province, district, village)",
        blank=True,
    )
    Id10059 = models.TextField("What was her/his marital status?", blank=True)
    Id10060_check = models.TextField("Is the date of marriage available?", blank=True)
    Id10060 = models.TextField("What was the date of marriage?", blank=True)
    Id10061 = models.TextField("What was the name of the father?", blank=True)
    Id10062 = models.TextField("What was the name of the mother?", blank=True)
    Id10063 = models.TextField(
        "What was her/his highest level of schooling?", blank=True
    )
    Id10064 = models.TextField("Was (s)he able to read and/or write?", blank=True)
    Id10065 = models.TextField(
        "What was her/his economic activity status in year prior to death?", blank=True
    )
    Id10066 = models.TextField(
        "What was her/his occupation, that is, what kind of work did (s)he mainly do?",
        blank=True,
    )
    Id10069 = models.TextField(
        "Is there a need to collect civil registration numbers on the deceased?",
        blank=True,
    )
    Id10069_a = models.TextField(
        "Do you have a Death Certificate from the Civil Registry?", blank=True
    )
    Id10070 = models.TextField("Death registration number/certificate", blank=True)
    Id10071_check = models.TextField(
        "Is the date of registration available?", blank=True
    )
    Id10071 = models.TextField("Date of registration", blank=True)
    Id10072 = models.TextField("Place of registration", blank=True)
    Id10073 = models.TextField("National identification number of deceased", blank=True)
    Id10476 = models.TextField(
        "Thank you for your information. Now can you please tell me in your own \
        words about the events that led to the death?",
        blank=True,
    )
    narrat_image = models.TextField("narrat_image", blank=True)
    Id10477 = MultiSelectField(
        "Select any of the following words that were mentioned as present in the narrative.",
        blank=True,
        choices=_select_510,
    )
    Id10478 = MultiSelectField(
        "Select any of the following words that were mentioned as present in the narrative.",
        blank=True,
        choices=_select_511,
    )
    Id10479 = MultiSelectField(
        "Select any of the following words that were mentioned as present in the narrative.",
        blank=True,
        choices=_select_512,
    )
    id10477_check = models.TextField(
        'It is not possible to select "Don\'t know" or "None of the above" \
        together with other options. Please go back and correct the selection.',
        blank=True,
    )
    id10478_check = models.TextField(
        'It is not possible to select "Don\'t know" or "None of the above" \
        together with other options. Please go back and correct the selection.',
        blank=True,
    )
    id10479_check = models.TextField(
        'It is not possible to select "Don\'t know" or "None of the above" \
        together with other options. Please go back and correct the selection.',
        blank=True,
    )
    Id10104 = models.TextField("Did the baby ever cry?", blank=True)
    Id10105 = models.TextField(
        "Did the baby cry immediately after birth, even if only a little bit?",
        blank=True,
    )
    Id10106 = models.TextField(
        "How many minutes after birth did the baby first cry?", blank=True
    )
    Id10107 = models.TextField("Did the baby stop being able to cry?", blank=True)
    Id10108 = models.TextField(
        "How many hours before death did the baby stop crying?", blank=True
    )
    Id10109 = models.TextField("Did the baby ever move?", blank=True)
    Id10110 = models.TextField("Did the baby ever breathe?", blank=True)
    Id10111 = models.TextField(
        "Did the baby breathe immediately after birth, even a little?", blank=True
    )
    Id10112 = models.TextField("Did the baby have a breathing problem?", blank=True)
    Id10113 = models.TextField(
        "Was the baby given assistance to breathe at birth?", blank=True
    )
    Id10114 = models.TextField(
        "If the baby didn't show any sign of life, was it born dead?", blank=True
    )
    Id10115 = models.TextField(
        "Were there any bruises or signs of injury on baby's body after the birth?",
        blank=True,
    )
    Id10116 = models.TextField(
        "Was the baby's body soft, pulpy and discoloured and the skin peeling away?",
        blank=True,
    )
    Id10077 = models.TextField(
        "Did (s)he suffer from any injury or accident that led to her/his death?",
        blank=True,
    )
    Id10079 = models.TextField("Was it a road traffic accident?", blank=True)
    Id10080 = models.TextField(
        "What was her/his role in the road traffic accident?", blank=True
    )
    Id10081 = models.TextField(
        "What was the counterpart that was hit during the road traffic accident?",
        blank=True,
    )
    Id10082 = models.TextField(
        "Was (s)he injured in a non-road transport accident?", blank=True
    )
    Id10083 = models.TextField("Was (s)he injured in a fall?", blank=True)
    Id10084 = models.TextField("Was there any poisoning?", blank=True)
    Id10085 = models.TextField("Did (s)he die of drowning?", blank=True)
    Id10086 = models.TextField(
        "Was (s)he injured by a bite or sting by venomous animal?", blank=True
    )
    Id10087 = models.TextField(
        "Was (s)he injured by an animal or insect (non-venomous)?", blank=True
    )
    Id10088 = models.TextField("What was the animal/insect?", blank=True)
    Id10089 = models.TextField("Was (s)he injured by burns/fire?", blank=True)
    Id10090 = models.TextField(
        "Was (s)he subject to violence (suicide, homicide, abuse)?", blank=True
    )
    Id10091 = models.TextField("Was (s)he injured by a firearm?", blank=True)
    Id10092 = models.TextField("Was (s)he stabbed, cut or pierced?", blank=True)
    Id10093 = models.TextField("Was (s)he strangled?", blank=True)
    Id10094 = models.TextField("Was (s)he injured by a blunt force?", blank=True)
    Id10095 = models.TextField("Was (s)he injured by a force of nature?", blank=True)
    Id10096 = models.TextField("Was it electrocution?", blank=True)
    Id10097 = models.TextField("Did (s)he encounter any other injury?", blank=True)
    Id10098 = models.TextField("Was the injury accidental?", blank=True)
    Id10099 = models.TextField("Was the injury self-inflicted?", blank=True)
    Id10100 = models.TextField(
        "Was the injury intentionally inflicted by someone else?", blank=True
    )
    Id10351 = models.TextField(
        "How many days old was the baby when the fatal illness started?", blank=True
    )
    Id10408 = models.TextField(
        "Before the illness that led to death, was the baby/the child growing normally?",
        blank=True,
    )
    Id10120_0 = models.TextField(
        "For how many days was (s)he ill before death?", blank=True
    )
    id10120_unit = models.TextField(
        "For how long was (s)he ill before death?", blank=True
    )
    Id10121 = models.TextField("Months", blank=True)
    Id10122 = models.TextField("Years", blank=True)
    Id10120_1 = models.TextField("Days", blank=True)
    Id10120 = models.TextField(
        "Calculated Field: Calculated number of Days with illness", blank=True
    )
    Id10123 = models.TextField("Did (s)he die suddenly?", blank=True)
    Id10125 = models.TextField(
        "Was there any diagnosis by a health professional of tuberculosis?", blank=True
    )
    Id10126 = models.TextField("Was an HIV test ever positive?", blank=True)
    Id10127 = models.TextField(
        "Was there any diagnosis by a health professional of AIDS?", blank=True
    )
    Id10128 = models.TextField(
        "Did (s)he have a recent positive test by a health professional for malaria?",
        blank=True,
    )
    Id10129 = models.TextField(
        "Did (s)he have a recent negative test by a health professional for malaria?",
        blank=True,
    )
    Id10130 = models.TextField(
        "Was there any diagnosis by a health professional of dengue fever?", blank=True
    )
    Id10131 = models.TextField(
        "Was there any diagnosis by a health professional of measles?", blank=True
    )
    Id10132 = models.TextField(
        "Was there any diagnosis by a health professional of high blood pressure?",
        blank=True,
    )
    Id10133 = models.TextField(
        "Was there any diagnosis by a health professional of heart disease?", blank=True
    )
    Id10134 = models.TextField(
        "Was there any diagnosis by a health professional of diabetes?", blank=True
    )
    Id10135 = models.TextField(
        "Was there any diagnosis by a health professional of asthma?", blank=True
    )
    Id10136 = models.TextField(
        "Was there any diagnosis by a health professional of epilepsy?", blank=True
    )
    Id10137 = models.TextField(
        "Was there any diagnosis by a health professional of cancer?", blank=True
    )
    Id10138 = models.TextField(
        "Was there any diagnosis by a health professional of Chronic \
        Obstructive Pulmonary Disease (COPD)?",
        blank=True,
    )
    Id10139 = models.TextField(
        "Was there any diagnosis by a health professional of dementia?", blank=True
    )
    Id10140 = models.TextField(
        "Was there any diagnosis by a health professional of depression?", blank=True
    )
    Id10141 = models.TextField(
        "Was there any diagnosis by a health professional of stroke?", blank=True
    )
    Id10142 = models.TextField(
        "Was there any diagnosis by a health professional of sickle cell disease?",
        blank=True,
    )
    Id10143 = models.TextField(
        "Was there any diagnosis by a health professional of kidney disease?",
        blank=True,
    )
    Id10144 = models.TextField(
        "Was there any diagnosis by a health professional of liver disease?", blank=True
    )
    Id10482 = models.TextField(
        "Was there any diagnosis by a health professional of COVID-19?", blank=True
    )
    Id10483 = models.TextField(
        "Did s(h)e have a recent test by a health professional for COVID-19?",
        blank=True,
    )
    Id10484 = models.TextField("What was the result?", blank=True)
    Id10147 = models.TextField("Did (s)he have a fever?", blank=True)
    Id10148_a = models.TextField("How many days did the fever last?", blank=True)
    Id10148_units = models.TextField("How long did the fever last?", blank=True)
    Id10148_b = models.TextField("Enter how long the fever lasted in days:", blank=True)
    Id10148_c = models.TextField(
        "Enter how long the fever lasted in months:", blank=True
    )
    Id10148 = models.TextField(
        "Calculated Field: How many days did the fever last?", blank=True
    )
    Id10149 = models.TextField("Did the fever continue until death?", blank=True)
    Id10150 = models.TextField("How severe was the fever?", blank=True)
    Id10151 = models.TextField("What was the pattern of the fever?", blank=True)
    Id10152 = models.TextField("Did (s)he have night sweats?", blank=True)
    Id10153 = models.TextField("Did (s)he have a cough?", blank=True)
    Id10154_units = models.TextField("For how long did (s)he have a cough?", blank=True)
    Id10154_a = models.TextField(
        "Enter how long (s)he had a cough in days:", blank=True
    )
    Id10154_b = models.TextField(
        "Enter how long (s)he had a cough in months:", blank=True
    )
    Id10154 = models.TextField(
        "Calculated Field: For how many days did (s)he have a cough?", blank=True
    )
    Id10155 = models.TextField("Was the cough productive, with sputum?", blank=True)
    Id10156 = models.TextField("Was the cough very severe?", blank=True)
    Id10157 = models.TextField("Did (s)he cough up blood?", blank=True)
    Id10158 = models.TextField(
        "Did (s)he make a whooping sound when coughing?", blank=True
    )
    Id10159 = models.TextField("Did (s)he have any difficulty breathing?", blank=True)
    Id10161_0 = models.TextField(
        "For how many days did the difficulty breathing last?", blank=True
    )
    id10161_unit = models.TextField(
        "For how long did the difficult breathing last?", blank=True
    )
    Id10161_1 = models.TextField(
        "Enter how long the difficult breathing lasted in days:", blank=True
    )
    Id10162 = models.TextField(
        "Enter how long the difficult breathing lasted in months:", blank=True
    )
    Id10163 = models.TextField(
        "Enter how long the difficult breathing lasted in years:", blank=True
    )
    Id10161 = models.TextField(
        "Calculated Field: Calculated number of Days with illness", blank=True
    )
    Id10165 = models.TextField(
        "Was the difficulty continuous or on and off?", blank=True
    )
    Id10166 = models.TextField(
        "During the illness that led to death, did (s)he have fast breathing?",
        blank=True,
    )
    Id10167_a = models.TextField(
        "For how many days did the fast breathing last?", blank=True
    )
    Id10167_units = models.TextField(
        "How long did the fast breathing last?", blank=True
    )
    Id10167_b = models.TextField(
        "Enter how long the fast breathing lasted in days:", blank=True
    )
    Id10167_c = models.TextField(
        "Enter how long the fast breathing lasted in months:", blank=True
    )
    Id10167 = models.TextField(
        "Calculated Field: How long did the fast breathing last?", blank=True
    )
    Id10168 = models.TextField("Did (s)he have breathlessness?", blank=True)
    Id10169_a = models.TextField(
        "For how many days did (s)he have breathlessness?", blank=True
    )
    Id10169_units = models.TextField(
        "How long did (s)he have breathlessness?", blank=True
    )
    Id10169_b = models.TextField(
        "Enter how long (s)he had breathlessness in days:", blank=True
    )
    Id10169_c = models.TextField(
        "Enter how long (s)he had breathlessness in months:", blank=True
    )
    Id10169 = models.TextField(
        "Calculated Field: How long did (s)he have breathlessness?", blank=True
    )
    Id10170 = models.TextField(
        "Was (s)he unable to carry out daily routines due to breathlessness?",
        blank=True,
    )
    Id10171 = models.TextField("Was (s)he breathless while lying flat?", blank=True)
    Id10172 = models.TextField(
        "Did you see the lower chest wall/ribs being pulled in as the child breathed in?",
        blank=True,
    )
    Id10173_nc = MultiSelectField(
        "During the illness that led to death did his/her breathing sound like \
        any of the following:",
        blank=True,
        choices=_select_501,
    )
    id10173_check = models.TextField(
        'It is not possible to select "Don\'t \
        know" or "refuse" together with other options. Please go back and \
        correct the selection.',
        blank=True,
    )
    Id10173_a = models.TextField(
        "During the illness that led to death did (s)he have wheezing?", blank=True
    )
    Id10173 = models.TextField(
        "Calculated Field: During the illness that led to death did his/her \
        breathing sound like any of the following:",
        blank=True,
    )
    Id10174 = models.TextField("Did (s)he have chest pain?", blank=True)
    Id10175 = models.TextField("Was the chest pain severe?", blank=True)
    Id10176 = models.TextField(
        "How many days before death did (s)he have chest pain?", blank=True
    )
    Id10178_unit = models.TextField("How long did the chest pain last?", blank=True)
    Id10178 = models.TextField(
        "Enter how long the chest pain lasted in minutes:", blank=True
    )
    Id10179 = models.TextField(
        "Enter how long the chest pain lasted in hours:", blank=True
    )
    Id10179_1 = models.TextField(
        "Enter how long the chest pain lasted in days:", blank=True
    )
    Id10181 = models.TextField(
        "Did (s)he have more frequent loose or liquid stools than usual?", blank=True
    )
    Id10182_units = models.TextField(
        "How long did (s)he have frequent loose or liquid stools?", blank=True
    )
    Id10182_a = models.TextField(
        "Enter how long (s)he had frequent loose or liquid stools in days:", blank=True
    )
    Id10182_b = models.TextField(
        "Enter how long (s)he had frequent loose or liquid stools in months:",
        blank=True,
    )
    Id10182 = models.TextField(
        "Calculated Field: For how many days did (s)he have frequent loose or liquid stools?",
        blank=True,
    )
    Id10183 = models.TextField(
        "How many stools did the baby or child have on the day that loose \
        liquid stools were most frequent?",
        blank=True,
    )
    Id10184_a = models.TextField(
        "How many days before death did the frequent loose or liquid stools start?",
        blank=True,
    )
    Id10184_units = models.TextField(
        "How long before death did the frequent loose or liquid stools start?",
        blank=True,
    )
    Id10184_b = models.TextField(
        "Enter how long before death the frequent loose or liquid stools started in days:",
        blank=True,
    )
    Id10184_c = models.TextField(
        "Enter how long before death the frequent loose or liquid stools started in months:",
        blank=True,
    )
    Id10185 = models.TextField(
        "Did the frequent loose or liquid stools continue until death?", blank=True
    )
    Id10186 = models.TextField(
        "At any time during the final illness was there blood in the stools?",
        blank=True,
    )
    Id10187 = models.TextField(
        "Was there blood in the stool up until death?", blank=True
    )
    Id10188 = models.TextField("Did (s)he vomit?", blank=True)
    Id10189 = models.TextField(
        "To clarify: Did (s)he vomit in the week preceding the death?", blank=True
    )
    Id10190_units = models.TextField(
        "How long before death did (s)he vomit?", blank=True
    )
    Id10190_a = models.TextField(
        "Enter how long before death(s)he vomited in days:", blank=True
    )
    Id10190_b = models.TextField(
        "Enter how long before death(s)he vomited in months:", blank=True
    )
    Id10191 = models.TextField("Was there blood in the vomit?", blank=True)
    Id10192 = models.TextField("Was the vomit black?", blank=True)
    Id10193 = models.TextField(
        "Did (s)he have any belly (abdominal) problem?", blank=True
    )
    Id10194 = models.TextField("Did (s)he have belly (abdominal) pain?", blank=True)
    Id10195 = models.TextField("Was the belly (abdominal) pain severe?", blank=True)
    id10196_unit = models.TextField(
        "For how long did (s)he have belly (abdominal) pain?", blank=True
    )
    Id10196 = models.TextField(
        "Enter how long (s)he had belly (abdominal) pain in hours:", blank=True
    )
    Id10197_a = models.TextField(
        "Enter how long (s)he had belly (abdominal) pain in days:", blank=True
    )
    Id10198 = models.TextField(
        "Enter how long (s)he had belly (abdominal) pain in months:", blank=True
    )
    Id10197 = models.TextField(
        "Calculated Field: Calculated number of Days with belly pain", blank=True
    )
    Id10199 = models.TextField(
        "Was the pain in the upper or lower belly (abdomen)?", blank=True
    )
    Id10200 = models.TextField(
        "Did (s)he have a more than usually protruding belly (abdomen)?", blank=True
    )
    Id10201_unit = models.TextField(
        "For how long before death did (s)he have a more than usually \
        protruding belly (abdomen)?",
        blank=True,
    )
    Id10201_a = models.TextField(
        "Enter how long before death (s)he had a more than usually protruding \
        belly (abdomen) in days:",
        blank=True,
    )
    Id10202 = models.TextField(
        "Enter how long before death (s)he had a more than usually protruding \
        belly (abdomen) in months:",
        blank=True,
    )
    Id10201 = models.TextField(
        "Calculated Field: Calculated number of Days with protruding belly (abdomen)",
        blank=True,
    )
    Id10203 = models.TextField(
        "How rapidly did (s)he develop the protruding belly (abdomen)?", blank=True
    )
    Id10204 = models.TextField(
        "Did (s)he have any mass in the belly (abdomen)?", blank=True
    )
    Id10205_unit = models.TextField(
        "For how long did (s)he have a mass in the belly (abdomen)?", blank=True
    )
    Id10205_a = models.TextField(
        "Enter how long (s)he had a mass in the belly (abdomen) in days:", blank=True
    )
    Id10206 = models.TextField(
        "Enter how long (s)he had a mass in the belly (abdomen) in months:", blank=True
    )
    Id10205 = models.TextField(
        "Calculated Field: Calculated number of Days with a mass in the belly (abdomen)",
        blank=True,
    )
    Id10207 = models.TextField("Did (s)he have a severe headache?", blank=True)
    Id10208 = models.TextField(
        "Did (s)he have a stiff neck during illness that led to death?", blank=True
    )
    Id10209_units = models.TextField(
        "How long before death did (s)he have stiff neck?", blank=True
    )
    Id10209_a = models.TextField(
        "Enter how long before death did (s)he have stiff neck in days:", blank=True
    )
    Id10209_b = models.TextField(
        "Enter how long before death did (s)he have stiff neck in months:", blank=True
    )
    Id10209 = models.TextField(
        "Calculated Field: For how many days before death did (s)he have stiff neck?",
        blank=True,
    )
    Id10210 = models.TextField(
        "Did (s)he have a painful neck during the illness that led to death?",
        blank=True,
    )
    Id10211_units = models.TextField(
        "How long before death did (s)he have a painful neck?", blank=True
    )
    Id10211_a = models.TextField(
        "Enter how long before death (s)he had a painful neck in days:", blank=True
    )
    Id10211_b = models.TextField(
        "Enter how long before death (s)he had a painful neck in months:", blank=True
    )
    Id10211 = models.TextField(
        "Calculated Field: For how many days before death did (s)he have a painful neck?",
        blank=True,
    )
    Id10212 = models.TextField("Did (s)he have mental confusion?", blank=True)
    Id10213_units = models.TextField(
        "How long did (s)he have mental confusion?", blank=True
    )
    Id10213_a = models.TextField(
        "Enter how long (s)he had mental confusion in days:", blank=True
    )
    Id10213_b = models.TextField(
        "Enter how long (s)he had mental confusion in months:", blank=True
    )
    Id10213 = models.TextField(
        "Calculated Field: For how many months did (s)he have mental confusion?",
        blank=True,
    )
    Id10214 = models.TextField(
        "Was (s)he unconscious during the illness that¬†led¬†to death?", blank=True
    )
    Id10215 = models.TextField(
        "Was (s)he unconscious for more than 24 hours before death?", blank=True
    )
    Id10216_units = models.TextField(
        "How long before death did unconsciousness start?", blank=True
    )
    Id10216_a = models.TextField(
        "Enter how long before death unconsciousness started in hours]?", blank=True
    )
    Id10216_b = models.TextField(
        "Enter how long before death unconsciousness started in days]?", blank=True
    )
    Id10216 = models.TextField(
        "Calculated Field: How many hours before death did unconsciousness start?",
        blank=True,
    )
    Id10217 = models.TextField(
        "Did the unconsciousness start suddenly, quickly (at least within a single day)?",
        blank=True,
    )
    Id10218 = models.TextField(
        "Did the unconsciousness continue until death?", blank=True
    )
    Id10219 = models.TextField("Did (s)he have convulsions?", blank=True)
    Id10220 = models.TextField(
        "Did (s)he experience any generalized convulsions or fits during the \
        illness that led to death?",
        blank=True,
    )
    Id10221 = models.TextField(
        "For how many minutes did the convulsions last?", blank=True
    )
    Id10222 = models.TextField(
        "Did (s)he become unconscious immediately after the convulsion?", blank=True
    )
    Id10223 = models.TextField("Did (s)he have any urine problems?", blank=True)
    Id10225 = models.TextField(
        "Did (s)he go to urinate more often than usual?", blank=True
    )
    Id10226 = models.TextField(
        "During the final illness did (s)he ever pass blood in the urine?", blank=True
    )
    Id10224 = models.TextField("Did (s)he stop urinating?", blank=True)
    Id10227 = models.TextField(
        "Did (s)he have sores or ulcers anywhere on the body?", blank=True
    )
    Id10228 = models.TextField("Did (s)he have sores?", blank=True)
    Id10229 = models.TextField("Did the sores have clear fluid or pus?", blank=True)
    Id10230 = models.TextField("Did (s)he have an ulcer (pit) on the foot?", blank=True)
    Id10231 = models.TextField("Did the ulcer on the foot ooze pus?", blank=True)
    Id10232_units = models.TextField(
        "How long did the ulcer on the foot ooze pus?", blank=True
    )
    Id10232_a = models.TextField(
        "Enter how long the ulcer on the foot oozed pus in days:", blank=True
    )
    Id10232_b = models.TextField(
        "Enter how long the ulcer on the foot oozed pus in months:", blank=True
    )
    Id10232 = models.TextField(
        "Calculated Field: For how many days did the ulcer on the foot ooze pus?",
        blank=True,
    )
    Id10233 = models.TextField(
        "During the illness that led to death, did (s)he have any skin rash?",
        blank=True,
    )
    Id10234 = models.TextField(
        "For how many days did (s)he have the skin rash?", blank=True
    )
    Id10235 = MultiSelectField("Where was the rash?", blank=True, choices=_select_135)
    id10235_check = models.TextField(
        'It is not possible to select "Doesn\'t Know" or "Refused to answer" \
        together with other options. Please go back and correct the selection.',
        blank=True,
    )
    Id10236 = models.TextField(
        "Did (s)he have measles rash (use local term)?", blank=True
    )
    Id10237 = models.TextField(
        "Did (s)he ever have shingles or herpes zoster?", blank=True
    )
    Id10238 = models.TextField(
        "During the illness that led to death, did her/his skin flake off in patches?",
        blank=True,
    )
    Id10239 = models.TextField(
        "During the illness that led to death, did he/she have areas of the \
        skin that turned black?",
        blank=True,
    )
    Id10240 = models.TextField(
        "During the illness that led to death, did he/she have areas of the \
        skin with redness and swelling?",
        blank=True,
    )
    Id10241 = models.TextField(
        "During the illness that led to death, did (s)he bleed from anywhere?",
        blank=True,
    )
    Id10242 = models.TextField(
        "Did (s)he bleed from the nose, mouth or anus?", blank=True
    )
    Id10243 = models.TextField("Did (s)he have noticeable weight loss?", blank=True)
    Id10244 = models.TextField("Was (s)he severely thin or wasted?", blank=True)
    Id10245 = models.TextField(
        "During the illness that led to death, did s/he have a whitish rash \
        inside the mouth or on the tongue?",
        blank=True,
    )
    Id10246 = models.TextField(
        "Did (s)he have stiffness of the whole body or was unable to open the mouth?",
        blank=True,
    )
    Id10247 = models.TextField("Did (s)he have puffiness of the face?", blank=True)
    Id10248_units = models.TextField(
        "How long did (s)he have puffiness of the face?", blank=True
    )
    Id10248_a = models.TextField(
        "Enter how long (s)he had puffiness of the face in days:", blank=True
    )
    Id10248_b = models.TextField(
        "Enter how long (s)he had puffiness of the face in months:", blank=True
    )
    Id10248 = models.TextField(
        "Calculated Field: For how many days did (s)he have puffiness of the face?",
        blank=True,
    )
    Id10249 = models.TextField(
        "During the illness that led to death, did (s)he have swollen legs or feet?",
        blank=True,
    )
    Id10250_units = models.TextField("How long did the swelling last?", blank=True)
    Id10250_a = models.TextField(
        "Enter how long the swelling lasted in days:", blank=True
    )
    Id10250_b = models.TextField(
        "Enter how long the swelling lasted in months:", blank=True
    )
    Id10250 = models.TextField(
        "Calculated Field: How many days did the swelling last?", blank=True
    )
    Id10251 = models.TextField("Did (s)he have both feet swollen?", blank=True)
    Id10252 = models.TextField(
        "Did (s)he have general puffiness all over his/her body?", blank=True
    )
    Id10253 = models.TextField("Did (s)he have any lumps?", blank=True)
    Id10254 = models.TextField(
        "Did (s)he have any lumps or lesions in the mouth?", blank=True
    )
    Id10255 = models.TextField("Did (s)he have any lumps on the neck?", blank=True)
    Id10256 = models.TextField("Did (s)he have any lumps on the armpit?", blank=True)
    Id10257 = models.TextField("Did (s)he have any lumps on the groin?", blank=True)
    Id10258 = models.TextField("Was (s)he in any way paralysed?", blank=True)
    Id10259 = models.TextField(
        "Did (s)he have paralysis of only one side of the body?", blank=True
    )
    Id10260 = MultiSelectField(
        "Which were the limbs or body parts paralysed?",
        blank=True,
        choices=_select_161,
    )
    id10260_check = models.TextField(
        'It is not possible to select "only one side paralysed" and "left and \
        right side" or "whole body" together. Please go back and correct the selection.',
        blank=True,
    )
    id10260_check2 = models.TextField(
        'It is not possible to select "Doesn\'t Know" or "Refused to answer" \
        together with other options. Please go back and correct the selection.',
        blank=True,
    )
    Id10261 = models.TextField("Did (s)he have difficulty swallowing?", blank=True)
    Id10262_units = models.TextField(
        "For how long before death did (s)he have difficulty swallowing?", blank=True
    )
    Id10262_a = models.TextField(
        "Enter how long before death (s)he had difficulty swallowing in days:",
        blank=True,
    )
    Id10262_b = models.TextField(
        "Enter how long before death (s)he had difficulty swallowing in months:",
        blank=True,
    )
    Id10262 = models.TextField(
        "Calculated Field: For how many days before death did (s)he have difficulty swallowing?",
        blank=True,
    )
    Id10263 = models.TextField(
        "Was the difficulty with swallowing with solids, liquids, or both?", blank=True
    )
    Id10264 = models.TextField("Did (s)he have pain upon swallowing?", blank=True)
    Id10265 = models.TextField(
        "Did (s)he have yellow discoloration of the eyes?", blank=True
    )
    Id10266_units = models.TextField(
        "For how long did (s)he have the yellow discoloration?", blank=True
    )
    Id10266_a = models.TextField(
        "Enter how long (s)he had the yellow discoloration in days:", blank=True
    )
    Id10266_b = models.TextField(
        "Enter how long (s)he had the yellow discoloration in months:", blank=True
    )
    Id10266 = models.TextField(
        "Calculated Field: For how many days did (s)he have the yellow discoloration?",
        blank=True,
    )
    Id10267 = models.TextField(
        "Did her/his hair change in color to a reddish or yellowish color?", blank=True
    )
    Id10268 = models.TextField(
        "Did (s)he look pale (thinning/lack of blood) or have pale palms, eyes or nail beds?",
        blank=True,
    )
    Id10269 = models.TextField("Did (s)he have sunken eyes?", blank=True)
    Id10270 = models.TextField(
        "Did (s)he drink a lot more water than usual?", blank=True
    )
    Id10271 = models.TextField(
        "Was the baby able to suckle or bottle-feed within the first 24 hours after birth?",
        blank=True,
    )
    Id10272 = models.TextField("Did the baby ever suckle in a normal way?", blank=True)
    Id10273 = models.TextField("Did the baby stop suckling?", blank=True)
    Id10274_a = models.TextField(
        "How many days after birth did the baby stop suckling?", blank=True
    )
    Id10274_units = models.TextField(
        "How long after birth did the baby stop suckling?", blank=True
    )
    Id10274_b = models.TextField(
        "Enter how long after birth the baby stopped suckling in days:", blank=True
    )
    Id10274_c = models.TextField(
        "Enter how long after birth the baby stopped suckling in months:", blank=True
    )
    Id10274 = models.TextField(
        "Calculated Field: How many days after birth did the baby stop suckling?",
        blank=True,
    )
    Id10275 = models.TextField(
        "Did the baby have convulsions starting within the first 24 hours of life?",
        blank=True,
    )
    Id10276 = models.TextField(
        "Did the baby have convulsions starting more than 24 hours after birth?",
        blank=True,
    )
    Id10277 = models.TextField(
        "Did the baby's body become stiff, with the back arched backwards?", blank=True
    )
    Id10278 = models.TextField(
        "During the illness that led to death, did the baby have a bulging or raised fontanelle?",
        blank=True,
    )
    Id10279 = models.TextField(
        "During the illness that led to death, did the baby have a sunken fontanelle?",
        blank=True,
    )
    Id10281 = models.TextField(
        "During the illness that led to death, did the baby become unresponsive or unconscious?",
        blank=True,
    )
    Id10282 = models.TextField(
        "Did the baby become unresponsive or unconscious soon after birth, within less than 24 hours?",
        blank=True,
    )
    Id10283 = models.TextField(
        "Did the baby become unresponsive or unconscious more than 24 hours after birth?",
        blank=True,
    )
    Id10284 = models.TextField(
        "During the illness that led to death, did the baby become cold to touch?",
        blank=True,
    )
    Id10285 = models.TextField(
        "How many days old was the baby when it started feeling cold to touch?",
        blank=True,
    )
    Id10286 = models.TextField(
        "During the illness that led to death, did the baby become lethargic after a period of normal activity?",
        blank=True,
    )
    Id10287 = models.TextField(
        "Did the baby have redness or pus drainage from the umbilical cord stump?",
        blank=True,
    )
    Id10288 = models.TextField(
        "During the illness that led to death, did the baby have skin ulcer(s) or pits?",
        blank=True,
    )
    Id10289 = models.TextField(
        "During the illness that led to death, did the baby have yellow skin, palms (hand) or soles (foot)?",
        blank=True,
    )
    Id10290 = models.TextField(
        "Did the baby or infant appear to be healthy and then just die suddenly?",
        blank=True,
    )
    Id10485 = models.TextField("Did (s)he suffer from extreme fatigue?", blank=True)
    Id10486 = models.TextField(
        "Did (s)he experience a new loss, change or decreased sense of smell or taste?",
        blank=True,
    )
    Id10294 = models.TextField(
        "Did she have any swelling or lump in the breast?", blank=True
    )
    Id10295 = models.TextField(
        "Did she have any ulcers (pits) in the breast?", blank=True
    )
    Id10296 = models.TextField("Did she ever have a period or menstruate?", blank=True)
    Id10297 = models.TextField(
        "When she had her period, did she have vaginal bleeding in between menstrual periods?",
        blank=True,
    )
    Id10298 = models.TextField("Was the bleeding excessive?", blank=True)
    Id10301 = models.TextField(
        "Was there excessive vaginal bleeding in the week prior to death?", blank=True
    )
    Id10299 = models.TextField(
        "Did her menstrual period stop naturally because of menopause or removal of uterus?",
        blank=True,
    )
    Id10302 = models.TextField(
        "At the time of death was her period overdue?", blank=True
    )
    Id10303 = models.TextField(
        "For how many weeks had her period been overdue?", blank=True
    )
    Id10300 = models.TextField(
        "Did she have vaginal bleeding after cessation of menstruation?", blank=True
    )
    Id10304 = models.TextField(
        "Did she have a sharp pain in her belly (abdomen) shortly before death?",
        blank=True,
    )
    Id10305 = models.TextField(
        "Was she pregnant or in labour at the time of death?", blank=True
    )
    Id10306 = models.TextField(
        "Did she die within 6 weeks of delivery, abortion or miscarriage?", blank=True
    )
    Id10307 = models.TextField(
        "Did this woman die more than 6 weeks after being pregnant or delivering a baby?",
        blank=True,
    )
    Id10308 = models.TextField(
        "Was this a woman who died less than 1 year after being pregnant or delivering a baby?",
        blank=True,
    )
    Id10309 = models.TextField("For how many months was she pregnant?", blank=True)
    Id10310 = models.TextField(
        "Please confirm, when she died, she was NEITHER pregnant NOR had delivered, \
        had an abortion, or miscarried within 12 months of when she died--is that right?",
        blank=True,
    )
    Id10310_check = models.TextField(
        'If the response is NO, DON\'T KNOW, OR REFUSED, it indicates some \
        uncertainty as to whether the cause of death could have been a maternal \
        or pregnancy-related cause. Go back to the question "Did she ever have \
        a period or menstruate?" and follow the process again. If it is confirmed \
        that the death was related to pregnancy, proceed with the next question \
        ‚ÄúDid she die during labour or delivery?‚Äù',
        blank=True,
    )
    Id10312 = models.TextField("Did she die during labour or delivery?", blank=True)
    Id10313 = models.TextField("Did she die after delivering a baby?", blank=True)
    Id10314 = models.TextField(
        "Did she die within 24 hours after delivery?", blank=True
    )
    Id10315_a = models.TextField(
        "Did she die within 6 weeks of childbirth?", blank=True
    )
    Id10315 = models.TextField(
        "Calculated Field: Did she die within 6 weeks of childbirth?", blank=True
    )
    Id10316 = models.TextField(
        "Did she give birth to a live baby (within 6 weeks of her death)?", blank=True
    )
    Id10317 = models.TextField(
        "Did she die during or after a multiple pregnancy?", blank=True
    )
    Id10318 = models.TextField(
        "Was she breastfeeding the child in the days before death?", blank=True
    )
    Id10319 = models.TextField(
        "How many births, including stillbirths, did she/the mother have before this baby?",
        blank=True,
    )
    Id10320 = models.TextField(
        "Had she had any previous Caesarean section?", blank=True
    )
    Id10321 = models.TextField(
        "During pregnancy, did she suffer from high blood pressure?", blank=True
    )
    Id10322 = models.TextField(
        "Did she have foul smelling vaginal discharge during pregnancy or after delivery?",
        blank=True,
    )
    Id10323 = models.TextField(
        "During the last 3 months of pregnancy, did she suffer from convulsions?",
        blank=True,
    )
    Id10324 = models.TextField(
        "During the last 3 months of pregnancy did she suffer from blurred vision?",
        blank=True,
    )
    Id10325 = models.TextField("Did bleeding occur while she was pregnant?", blank=True)
    Id10326 = models.TextField(
        "Was there vaginal bleeding during the first 6 months of pregnancy?", blank=True
    )
    Id10327 = models.TextField(
        "Was there vaginal bleeding during the last 3 months of pregnancy but \
        before labour started?",
        blank=True,
    )
    Id10328 = models.TextField(
        "Did she have excessive bleeding during labour or delivery?", blank=True
    )
    Id10329 = models.TextField(
        "Did she have excessive bleeding after delivery or abortion?", blank=True
    )
    Id10330 = models.TextField("Was the placenta completely delivered?", blank=True)
    Id10331 = models.TextField(
        "Did she deliver or try to deliver an abnormally positioned baby?", blank=True
    )
    Id10332 = models.TextField("For how many hours was she in labour?", blank=True)
    Id10333 = models.TextField(
        "Did she attempt to terminate the pregnancy?", blank=True
    )
    Id10334 = models.TextField(
        "Did she recently have a pregnancy that ended in an abortion \
        (spontaneous or induced)?",
        blank=True,
    )
    Id10335 = models.TextField("Did she die during an abortion?", blank=True)
    Id10336 = models.TextField(
        "Did she die within 6 weeks of having an abortion?", blank=True
    )
    Id10337 = models.TextField(
        "Where did she give birth / complete the miscarriage / have the abortion?",
        blank=True,
    )
    Id10338 = models.TextField(
        "Did she receive professional assistance during the delivery?", blank=True
    )
    Id10339 = models.TextField(
        "Who delivered the baby / completed the miscarriage / performed the abortion?",
        blank=True,
    )
    Id10342 = models.TextField(
        "Was the delivery normal vaginal, without forceps or vacuum?", blank=True
    )
    Id10343 = models.TextField(
        "Was the delivery vaginal, with forceps or vacuum?", blank=True
    )
    Id10344 = models.TextField("Was the delivery a Caesarean section?", blank=True)
    Id10347 = models.TextField(
        "Was the baby born more than one month early?", blank=True
    )
    Id10340 = models.TextField(
        "Did she have an operation to remove her uterus shortly before death?",
        blank=True,
    )
    Id10352_units = models.TextField(
        "How old was the child when the fatal illness started?", blank=True
    )
    Id10352_a = models.TextField(
        "Enter how old the child was when the fatal illness started in months:",
        blank=True,
    )
    Id10352_b = models.TextField(
        "Enter how old the child was when the fatal illness started in years:",
        blank=True,
    )
    Id10352 = models.TextField(
        "Calculated Field: How many years old was the child when the fatal illness started?",
        blank=True,
    )
    Id10354 = models.TextField("Was the child part of a multiple birth?", blank=True)
    Id10355 = models.TextField(
        "Was the child the first, second, or later in the birth order?", blank=True
    )
    Id10356 = models.TextField("Is the mother still alive?", blank=True)
    Id10357 = models.TextField(
        "Did the mother die before, during or after the delivery?", blank=True
    )
    Id10358_units = models.TextField(
        "How long after the delivery did the mother die?", blank=True
    )
    Id10358 = models.TextField(
        "How many months after the delivery did the mother die?", blank=True
    )
    Id10359 = models.TextField(
        "How many days after the delivery did the mother die?", blank=True
    )
    Id10359_a = models.TextField(
        "How many weeks after the delivery did the mother die?", blank=True
    )
    Id10360 = models.TextField("Where was the deceased born?", blank=True)
    Id10361 = models.TextField(
        "Did you/the mother receive professional assistance during the delivery?",
        blank=True,
    )
    Id10362 = models.TextField("At birth, was the baby of usual size?", blank=True)
    Id10363 = models.TextField(
        "At birth, was the baby smaller than usual, (weighing under 2.5 kg)?",
        blank=True,
    )
    Id10364 = models.TextField(
        "At birth, was the baby very much smaller than usual, (weighing under 1 kg)?",
        blank=True,
    )
    Id10365 = models.TextField(
        "At birth, was the baby larger than usual, (weighing over 4.5 kg)?", blank=True
    )
    id1036X_check = models.TextField(
        'It is not possible to select "No usual size at Birth", "No weighing \
        under 2.5 kg" and "No weighing over 4.5 kg" together. Please go back \
        and correct the selection.',
        blank=True,
    )
    Id10366_unit = models.TextField(
        "What was the weight of the deceased at \
        birth? [Enter weight in:]",
        blank=True,
    )
    Id10366_a = models.TextField(
        "What was the weight of the deceased at \
        birth? [Enter weight in grammes:]",
        blank=True,
    )
    Id10366_b = models.TextField(
        "What was the weight of the deceased at birth? \
        [Enter weight in kilograms:]",
        blank=True,
    )
    Id10366 = models.TextField(
        "What was the weight (in grammes) of the deceased at birth?", blank=True
    )
    Id10367 = models.TextField(
        "How many months long was the pregnancy before the child was born?", blank=True
    )
    Id10368 = models.TextField(
        "Were there any complications in the late part of the pregnancy \
        (defined as the last 3 months, before labour)?",
        blank=True,
    )
    Id10369 = models.TextField(
        "Were there any complications during labour or delivery?", blank=True
    )
    Id10370 = models.TextField(
        "Was any part of the baby physically abnormal at time of delivery? \
        (for example: body part too large or too small, additional growth on body)?",
        blank=True,
    )
    Id10371 = models.TextField(
        "Did the baby/ child have a swelling or defect on the back at time of birth?",
        blank=True,
    )
    Id10372 = models.TextField(
        "Did the baby/ child have a very large head at time of birth?", blank=True
    )
    Id10373 = models.TextField(
        "Did the baby/ child have a very small head at time of birth?", blank=True
    )
    Id10394 = models.TextField(
        "How many births, including stillbirths, did the baby's mother have before this baby?",
        blank=True,
    )
    Id10376 = models.TextField(
        "Was the baby moving in the last few days before the birth?", blank=True
    )
    Id10377 = models.TextField(
        "Did the baby stop moving in the womb before labour started?", blank=True
    )
    Id10379_unit = models.TextField(
        "How long before labour did you/the mother last feel the baby move?", blank=True
    )
    Id10379 = models.TextField(
        "Enter how long before labour did you/the mother last feel the baby move in days:",
        blank=True,
    )
    Id10380 = models.TextField(
        "Enter how long before labour did you/the mother last feel the baby move in hours:",
        blank=True,
    )
    Id10382 = models.TextField(
        "How many hours did labour and delivery take?", blank=True
    )
    Id10383 = models.TextField(
        "Was the baby born 24 hours or more after the water broke?", blank=True
    )
    Id10384 = models.TextField("Was the liquor foul smelling?", blank=True)
    Id10385 = models.TextField(
        "What was the colour of the liquor when the water broke?", blank=True
    )
    Id10387 = models.TextField(
        "Was the delivery normal vaginal, without forceps or vacuum?", blank=True
    )
    Id10388 = models.TextField(
        "Was the delivery vaginal, with forceps or vacuum?", blank=True
    )
    Id10389 = models.TextField("Was the delivery a Caesarean section?", blank=True)
    id10389_check = models.TextField(
        'It is not possible to select "No" to all three previous questions. \
        Please go back and review the answers.',
        blank=True,
    )
    Id10391 = models.TextField(
        "Did you/the mother receive any vaccinations since reaching adulthood \
        including during this pregnancy?",
        blank=True,
    )
    Id10392 = models.TextField("How many doses?", blank=True)
    Id10393 = models.TextField(
        "Did you/the mother receive tetanus toxoid (TT) vaccine?", blank=True
    )
    Id10395 = models.TextField(
        "During labour, did the baby's mother suffer from fever?", blank=True
    )
    Id10396 = models.TextField(
        "During the last 3 months of pregnancy, labour or delivery, did \
        you/the baby's mother suffer from high blood pressure?",
        blank=True,
    )
    Id10397 = models.TextField(
        "Did you/the baby's mother have diabetes mellitus?", blank=True
    )
    Id10398 = models.TextField(
        "Did you/the baby's mother have foul smelling vaginal discharge during \
        pregnancy or after delivery?",
        blank=True,
    )
    Id10399 = models.TextField(
        "During the last 3 months of pregnancy, labour or delivery, did \
        you/the baby's mother suffer from convulsions?",
        blank=True,
    )
    Id10400 = models.TextField(
        "During the last 3 months of pregnancy did you/the baby's mother \
        suffer from blurred vision?",
        blank=True,
    )
    Id10401 = models.TextField(
        "Did you/the baby's mother have severe anemia?", blank=True
    )
    Id10402 = models.TextField(
        "Did you/the baby's mother have vaginal bleeding during the last 3 \
        months of pregnancy but before labour started?",
        blank=True,
    )
    Id10403 = models.TextField(
        "Did the baby's bottom, feet, arm or hand come out of the vagina before its head?",
        blank=True,
    )
    Id10404 = models.TextField(
        "Was the umbilical cord wrapped more than once around the neck of the child at birth?",
        blank=True,
    )
    Id10405 = models.TextField("Was the umbilical cord delivered first?", blank=True)
    Id10406 = models.TextField("Was the baby blue in colour at birth?", blank=True)
    Id10411 = models.TextField("Did (s)he drink alcohol?", blank=True)
    Id10412 = models.TextField("Did (s)he use tobacco?", blank=True)
    Id10413 = models.TextField(
        "Did (s)he smoke tobacco (cigarette, cigar, pipe, etc.)?", blank=True
    )
    Id10414 = models.TextField("What kind of tobacco did (s)he use ?", blank=True)
    id10414_check = models.TextField(
        'It is not possible to select cigarettes or pipe and "no" to \
        "Did (s)he smoke tobacco?". Please go back and correct the selections.',
        blank=True,
    )
    Id10415 = models.TextField("How many cigarettes did (s)he smoke daily?", blank=True)
    Id10416 = models.TextField(
        "How many times did (s)he use tobacco products each day?", blank=True
    )
    Id10418 = models.TextField(
        "Did (s)he receive any treatment for the illness that led to death?", blank=True
    )
    Id10419 = models.TextField("Did (s)he receive oral rehydration salts?", blank=True)
    Id10420 = models.TextField(
        "Did (s)he receive (or need) intravenous fluids (drip) treatment?", blank=True
    )
    Id10421 = models.TextField(
        "Did (s)he receive (or need) a blood transfusion?", blank=True
    )
    Id10422 = models.TextField(
        "Did (s)he receive (or need) treatment/food through a tube passed through the nose?",
        blank=True,
    )
    Id10423 = models.TextField(
        "Did (s)he receive (or need) injectable antibiotics?", blank=True
    )
    Id10424 = models.TextField(
        "Did (s)he receive (or need) antiretroviral therapy (ART)?", blank=True
    )
    Id10425 = models.TextField(
        "Did (s)he have (or need) an operation for the illness?", blank=True
    )
    Id10426 = models.TextField(
        "Did (s)he have the operation within 1 month before death?", blank=True
    )
    Id10427 = models.TextField(
        "Was (s)he discharged from hospital very ill?", blank=True
    )
    Id10428 = models.TextField("Did (s)he receive any immunizations?", blank=True)
    Id10429 = models.TextField("Do you have the child's vaccination card?", blank=True)
    Id10430 = models.TextField(
        "Can I see the vaccination card (note the vaccines the child received)?",
        blank=True,
    )
    Id10431 = MultiSelectField(
        "Select EPI vaccines done",
        blank=True,
        choices=_select_vaccines,
    )
    id10431_check = models.TextField(
        'It is not possible to select "No vaccines", "Don\'t know" or "refuse" \
        together with other options. Please go back and correct the selection.',
        blank=True,
    )
    Id10432 = models.TextField(
        "Was care sought outside the home while (s)he had this illness?", blank=True
    )
    Id10433 = MultiSelectField(
        "Where or from whom did you seek care?",
        blank=True,
        choices=_select_322,
    )
    id10433_check = models.TextField(
        'It is not possible to select "Don\'t know" or "refuse" together with \
        other options. Please go back and correct the selection.',
        blank=True,
    )
    Id10434 = models.TextField(
        "What was the name and address of any hospital, health center or \
        clinic where care was sought",
        blank=True,
    )
    Id10435 = models.TextField(
        "Did a health care worker tell you the cause of death?", blank=True
    )
    Id10436 = models.TextField("What did the health care worker say?", blank=True)
    Id10437 = models.TextField(
        "Do you have any health records that belonged to the deceased?", blank=True
    )
    Id10438 = models.TextField("Can I see the health records?", blank=True)
    Id10439_check = models.TextField(
        "Is the date of the most recent (last) visit available?", blank=True
    )
    Id10439 = models.TextField(
        "Record the date of the most recent (last) visit", blank=True
    )
    Id10440_check = models.TextField(
        "Is the date of the second most recent visit available?", blank=True
    )
    Id10440 = models.TextField(
        "Record the date of the second most recent visit", blank=True
    )
    Id10441_check = models.TextField(
        "Is the date of the last note on the health records available?", blank=True
    )
    Id10441 = models.TextField(
        "Record the date of the last note on the health records", blank=True
    )
    Id10442 = models.TextField(
        "Record the weight (in kilogrammes) written at the most recent (last) visit",
        blank=True,
    )
    Id10443 = models.TextField(
        "Record the weight (in kilogrammes) written at the second most recent visit",
        blank=True,
    )
    Id10444 = models.TextField(
        "Transcribe the last note on the health records", blank=True
    )
    Id10445 = models.TextField(
        "Has the deceased's (biological) mother ever been tested for HIV?", blank=True
    )
    Id10446 = models.TextField(
        "Has the deceased's (biological) mother ever been told she had \
        HIV/AIDS by a health worker?",
        blank=True,
    )
    Id10450 = models.TextField(
        "In the final days before death, did s/he travel to a hospital or health facility?",
        blank=True,
    )
    Id10451 = models.TextField(
        "Did (s)he use motorized transport to get to the hospital or health facility?",
        blank=True,
    )
    Id10452 = models.TextField(
        "Were there any problems during admission to the hospital or health facility?",
        blank=True,
    )
    Id10453 = models.TextField(
        "Were there any problems with the way (s)he was treated (medical treatment, \
        procedures, interpersonal attitudes, respect, dignity) in the hospital or health facility?",
        blank=True,
    )
    Id10454 = models.TextField(
        "Were there any problems getting medications or diagnostic tests in \
        the hospital or health facility?",
        blank=True,
    )
    Id10455 = models.TextField(
        "Does it take more than 2 hours to get to the nearest hospital or \
        health facility from the deceased's household?",
        blank=True,
    )
    Id10456 = models.TextField(
        "In the final days before death, were there any doubts about whether \
        medical care was needed?",
        blank=True,
    )
    Id10457 = models.TextField(
        "In the final days before death, was traditional medicine used?", blank=True
    )
    Id10458 = models.TextField(
        "In the final days before death, did anyone use a telephone or cell \
        phone to call for help?",
        blank=True,
    )
    Id10459 = models.TextField(
        "Over the course of illness, did the total costs of care and treatment \
        prohibit other household payments?",
        blank=True,
    )
    Id10462 = models.TextField(
        "Was a medical certificate of cause of death issued?", blank=True
    )
    Id10463 = models.TextField(
        "Can I see the medical certificate of cause of death?", blank=True
    )
    Id10464 = models.TextField(
        "Record the immediate cause of death from the certificate (line 1a)", blank=True
    )
    Id10465 = models.TextField("Duration (Ia):", blank=True)
    Id10466 = models.TextField(
        "Record the first antecedent cause of death from the certificate (line 1b)",
        blank=True,
    )
    Id10467 = models.TextField("Duration (Ib):", blank=True)
    Id10468 = models.TextField(
        "Record the second antecedent cause of death from the certificate (line 1c)",
        blank=True,
    )
    Id10469 = models.TextField("Duration (Ic):", blank=True)
    Id10470 = models.TextField(
        "Record the third antecedent cause of death from the certificate (line 1d)",
        blank=True,
    )
    Id10471 = models.TextField("Duration (Id):", blank=True)
    Id10472 = models.TextField(
        "Record the contributing cause(s) of death from the certificate (part 2)",
        blank=True,
    )
    Id10473 = models.TextField("Duration (part2):", blank=True)
    Id10481 = models.TextField("Interview End Datetime", blank=True)
    geopoint = models.TextField("geopoint", blank=True)
    comment = models.TextField("Comment", blank=True)
    # Track the history of changes to each verbal autopsy
    history = HistoricalRecords(excluded_fields=["unique_va_identifier", "duplicate"])
    # Automatically set timestamps
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    # Supports soft delete of duplicate records
    # deleted_at inherited from SoftDeletionModel
    unique_va_identifier = models.TextField(
        "md5 hash of the unique_va_identifiers", blank=True
    )
    duplicate = models.BooleanField(
        "Marks the record as duplicate", blank=True, default=False
    )

    # function to tell if VA had any coding errors
    def any_errors(self):
        return self.coding_issues.filter(severity="error").exists()

    # function to tell if VA had any coding warnings
    def any_warnings(self):
        return self.coding_issues.filter(severity="warning").exists()

    # def clean(self):
    # TODO: fill this out with cleaning operations we actually want to do
    #       return

    def set_null_location(self, null_name="Unknown"):
        # to handle passing null_name=None
        if not null_name:
            null_name = "Unknown"
        # first, check if null location exists. If not, create one.
        null_location = Location.objects.filter(name=null_name).first()
        if not null_location:
            # if no locations, make null location root. Otherwise, add child to root
            if not Location.objects.exists():
                Location.add_root(name=null_name, location_type="facility")
            else:
                Location.objects.first().add_child(
                    name=null_name, location_type="facility"
                )
            # find new location we just created
            null_location = Location.objects.get(name=null_name)
        self.location = null_location

    @staticmethod
    def auto_detect_duplicates():
        return questions_to_autodetect_duplicates()

    def any_identifier_changed(self, saved_va):
        for identifier in questions_to_autodetect_duplicates():
            if getattr(self, identifier) != getattr(saved_va, identifier):
                return True
        return False

    def generate_unique_identifier_hash(self):
        md5 = hashlib.md5()
        unique_identifier_string = "".join(
            [
                str(getattr(self, identifier))
                for identifier in questions_to_autodetect_duplicates()
            ]
        )
        md5.update(unique_identifier_string.encode())
        self.unique_va_identifier = md5.hexdigest()

    @classmethod
    def mark_duplicates(cls):
        duplicate_vas = (
            cls.objects.values("unique_va_identifier")
            .annotate(unique_va_identifier_count=Count("unique_va_identifier"))
            .filter(unique_va_identifier_count__gt=1)
        )
        if duplicate_vas.exists():
            for identifiers_hash in duplicate_vas:
                vas = VerbalAutopsy.objects.filter(
                    unique_va_identifier=identifiers_hash["unique_va_identifier"]
                ).order_by("created")
                # Skip the first record: this is the oldest record one and the one we will not mark as duplicate
                duplicate_vas = []
                for va in vas[1:]:
                    va.duplicate = True
                    duplicate_vas.append(va)

                VerbalAutopsy.objects.bulk_update(duplicate_vas, ["duplicate"])

    def update_duplicates_with_changed_unique_identifier(self, saved_va):
        # Given a set of duplicate VAs, we designate the oldest one as the non-duplicate record.
        # If the record that we are updating is the oldest amongst all of the records with the same
        # unique_va_identifier, it is the only record in the query set with duplicate = False.
        # We need to determine which record is the oldest amongst the remaining records that share the
        # saved_va's unique_va_identifier and mark that as duplicate = False.
        oldest_va_with_previous_unique_va_identifier = (
            VerbalAutopsy.objects.filter(
                unique_va_identifier=saved_va.unique_va_identifier
            )
            .exclude(id=self.pk)
            .order_by("created")
            .first()
        )

        if oldest_va_with_previous_unique_va_identifier:
            oldest_va_with_previous_unique_va_identifier.duplicate = False
            oldest_va_with_previous_unique_va_identifier.save()

        # Get the oldest pre-existing VAs that matches self.unique_identifier_hash, the identifier we are updating to
        oldest_va_with_new_unique_va_identifier = (
            VerbalAutopsy.objects.filter(unique_va_identifier=self.unique_va_identifier)
            .order_by("created")
            .first()
        )

        if oldest_va_with_new_unique_va_identifier:
            if oldest_va_with_new_unique_va_identifier.created < self.created:
                self.duplicate = True
            else:
                oldest_va_with_new_unique_va_identifier.duplicate = True
                self.duplicate = False
                oldest_va_with_new_unique_va_identifier.save()
        else:
            self.duplicate = False

    def handle_update_duplicates(self):
        # If the Verbal Autopsy already exists and we are updating it
        if self.pk:
            saved_va = VerbalAutopsy.objects.get(pk=self.pk)

            if self.any_identifier_changed(saved_va):
                # Generate a new unique_identifier_hash since one of the constituent fields has changed
                self.generate_unique_identifier_hash()
                self.update_duplicates_with_changed_unique_identifier(saved_va)
        # If the Verbal Autopsy does not exist and we are creating it
        else:
            # Generate a unique_identifier_hash
            self.generate_unique_identifier_hash()

            # Get any pre-existing VAs that match self.unique_identifier_hash
            vas_with_new_unique_va_identifier = VerbalAutopsy.objects.filter(
                unique_va_identifier=self.unique_va_identifier
            )

            # If any pre-existing VAs match self.unique_identifier_hash, they are guaranteed to be older
            # than this record because we are creating it now. Thus, this record is a duplicate because
            # we always designate the oldest record as the non-duplicate
            if vas_with_new_unique_va_identifier.exists():
                self.duplicate = True
            else:
                self.duplicate = False

    def save(self, *args, **kwargs):
        if VerbalAutopsy.auto_detect_duplicates():
            self.handle_update_duplicates()

        super().save(*args, **kwargs)


# Parses the comma-separated list string in settings.QUESTIONS_TO_AUTODETECT_DUPLICATES into a Python list
# Validates that the question IDs passed into settings.QUESTIONS_TO_AUTODETECT_DUPLICATES match a field in the VA model
# If a question ID that is not a field on the VA model is encountered, skip it
def questions_to_autodetect_duplicates():
    if not settings.QUESTIONS_TO_AUTODETECT_DUPLICATES:
        return []

    questions = [
        q.strip() for q in settings.QUESTIONS_TO_AUTODETECT_DUPLICATES.split(",")
    ]
    validated_questions = []
    valid_field = None

    for q in questions:
        with contextlib.suppress(FieldDoesNotExist):
            valid_field = VerbalAutopsy._meta.get_field(q)
        if valid_field:
            validated_questions.append(q)

    return validated_questions


class CODCodesDHIS(models.Model):
    codsource = models.TextField(blank=False)
    codcode = models.TextField(blank=False)
    codname = models.TextField(blank=False)
    codid = models.TextField(blank=False)

    def __str__(self):
        return self.codname


# Soft-deleting a Verbal Autopsy does not result in cascade deletion the way that true database-level deletes do
# Add a manager for each of the models where on_delete=models.CASCADE
# Adding an individual manager works if we only have a small number of related models, but is a brittle solution
# TODO: Determine a way to handle cascading soft deletes globally/generically
class DhisStatusManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(verbalautopsy__deleted_at__isnull=True)


class CauseOfDeathManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(verbalautopsy__deleted_at__isnull=True)


class CauseCodingIssueManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(verbalautopsy__deleted_at__isnull=True)


class DhisStatus(models.Model):
    verbalautopsy = models.ForeignKey(
        VerbalAutopsy, related_name="dhisva", on_delete=models.CASCADE
    )
    vaid = models.TextField(blank=False)
    edate = models.DateTimeField(auto_now_add=True)
    status = models.TextField(blank=False, default="SUCCESS")
    objects = DhisStatusManager()

    def __str__(self):
        return self.vaid


class CauseOfDeath(models.Model):
    # One VerbalAutopsy can have multiple causes of death (through different algorithms)
    verbalautopsy = models.ForeignKey(
        VerbalAutopsy, related_name="causes", on_delete=models.CASCADE
    )
    # Track the cause and the algorithm that provided the cause
    cause = models.TextField()
    # TODO: do we want the algorithm as a string or by referring to an algorithm table?
    algorithm = models.TextField()
    # Store the settings used for this particular coding run
    # NOTE: by using JSONField we tie ourselves to postgres
    settings = JSONField()
    # Track the history of changes to each verbal autopsy cause of death coding
    # TODO: confirm that we need a history of this
    history = HistoricalRecords()
    # Automatically set timestamps
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    objects = CauseOfDeathManager()

    def __str__(self):
        return self.cause


class CauseCodingIssue(models.Model):
    # One VerbalAutopsy can have multiple coding issues
    verbalautopsy = models.ForeignKey(
        VerbalAutopsy, related_name="coding_issues", on_delete=models.CASCADE
    )
    text = models.TextField()
    SEVERITY_OPTIONS = ["error", "warning"]
    severity = models.CharField(
        max_length=7, choices=[(option, option) for option in SEVERITY_OPTIONS]
    )
    # We track which algorithm and the settings for that algorithm
    # NOTE: this is a de-normalized approach for convenience, which should still
    # scale reasonably
    algorithm = models.TextField()
    # NOTE: by using JSONField we tie ourselves to postgres
    settings = JSONField()
    # Automatically set timestamps
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    objects = CauseCodingIssueManager()

    def __str__(self):
        return self.text
