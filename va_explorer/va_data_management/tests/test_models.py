import pytest

from va_explorer.tests.factories import VerbalAutopsyFactory

pytestmark = pytest.mark.django_db

def test_save_mark_duplicates_with_autodetect_duplicates(settings):
    settings.QUESTIONS_TO_AUTODETECT_DUPLICATES = "Id10017, Id10018, Id10019, Id10020, Id10022, Id10023"

    va1 = VerbalAutopsyFactory.create(Id10017='Bob', Id10018='Jones', Id10019='Male', Id10020='Yes', Id10021='1/1/60',
                                      Id10022='Yes', Id10023='1/5/21', instanceid='00')
    va2 = VerbalAutopsyFactory.create(Id10017='Bob', Id10018='Jones', Id10019='Male', Id10020='Yes', Id10021='1/1/60',
                                      Id10022='Yes', Id10023='1/5/21', instanceid='01')
    va3 = VerbalAutopsyFactory.create(Id10017='Bob', Id10018='Jones', Id10019='Male', Id10020='Yes', Id10021='1/1/60',
                                      Id10022='Yes', Id10023='1/5/21', instanceid='02')
    va4 = VerbalAutopsyFactory.create(Id10017='Barb', Id10018='Jones', Id10019='Female', Id10020='Yes',
                                      Id10021='1/1/60', Id10022='Yes', Id10023='1/5/21', instanceid='03')
    va5 = VerbalAutopsyFactory.create(Id10017='Barb', Id10018='Jones', Id10019='Female', Id10020='Yes',
                                      Id10021='1/1/60', Id10022='Yes', Id10023='1/5/21', instanceid='04')
    va6 = VerbalAutopsyFactory.create(Id10017='Tom', Id10018='Jones', Id10019='Male', Id10020='No', Id10021='',
                                      Id10022='No', Id10023='', instanceid='05')

    va1.refresh_from_db()
    va2.refresh_from_db()
    va3.refresh_from_db()
    va4.refresh_from_db()
    va5.refresh_from_db()
    va6.refresh_from_db()

    assert not va1.duplicate
    assert va2.duplicate
    assert va3.duplicate
    assert not va4.duplicate
    assert va5.duplicate
    assert not va6.duplicate


def test_save_updates_unique_va_identifier_with_autodetect_duplicates(settings):
    settings.QUESTIONS_TO_AUTODETECT_DUPLICATES = "Id10017, Id10018, Id10019, Id10020, Id10021, Id10022, Id10023"

    va1 = VerbalAutopsyFactory.create(Id10017='Bob', Id10018='Jones', Id10019='Male', Id10020='Yes', Id10021='1/1/60',
                               Id10022='Yes', Id10023='1/5/21', instanceid='00'
                               )

    assert va1.unique_va_identifier == '840ba941ac6e608962f86eb05659bad1'

    va1.Id10017 = 'Robert'
    va1.save()
    assert va1.unique_va_identifier == '690b7d0bd136e0e4f7e732b86cbeb12e'

    va1.Id10018 = 'Jonesy'
    va1.save()
    assert va1.unique_va_identifier == '811f7f36f5da61dae92f12caa46ffad9'

    va1.Id10019 = 'dk'
    va1.save()
    assert va1.unique_va_identifier == '47c75220e6a1e7594e98bba4f0d0c003'

    va1.Id10020 = 'dk'
    va1.save()
    assert va1.unique_va_identifier == 'a567709589e739616a6b77441d871767'

    va1.Id10021 = '1/1/61'
    va1.save()
    assert va1.unique_va_identifier == '81616374fab861f1630b288a30cd0447'

    va1.Id10022 = 'No'
    va1.save()
    assert va1.unique_va_identifier == '52b23a15634033697d1fa7d3988f3f27'

    va1.Id10023 = ''
    va1.save()
    assert va1.unique_va_identifier == '3df591b678ea5e730966fc63ac77b687'

    va1.Id10002 = 'yes'
    va1.save()
    assert va1.unique_va_identifier == '3df591b678ea5e730966fc63ac77b687'

def test_save_does_not_populate_unique_va_identifier_without_autodetect_duplicates(settings):
    settings.QUESTIONS_TO_AUTODETECT_DUPLICATES = None

    va1 = VerbalAutopsyFactory.create(Id10017='Bob', Id10018='Jones', Id10019='Male', Id10020='Yes', Id10021='1/1/60',
                               Id10022='Yes', Id10023='1/5/21', instanceid='00'
                               )

    assert va1.unique_va_identifier == ''


def test_save_updates_duplicates_with_autodetect_duplicates(settings):
    settings.QUESTIONS_TO_AUTODETECT_DUPLICATES = "Id10017, Id10018, Id10019, Id10020, Id10021, Id10022, Id10023"


    va1 = VerbalAutopsyFactory.create(Id10017='Bob', Id10018='Jones', Id10019='Male', Id10020='Yes', Id10021='1/1/60',
                               Id10022='Yes', Id10023='1/5/21', instanceid='00'
                               )
    va2 = VerbalAutopsyFactory.create(Id10017='Bob', Id10018='Jones', Id10019='Male', Id10020='Yes', Id10021='1/1/60',
                               Id10022='Yes', Id10023='1/5/21', instanceid='00'
                               )
    va3 = VerbalAutopsyFactory.create(Id10017='Bob', Id10018='Jones', Id10019='Male', Id10020='Yes', Id10021='1/1/60',
                               Id10022='Yes', Id10023='1/5/21', instanceid='00'
                               )
    va4 = VerbalAutopsyFactory.create(Id10017='Bob', Id10018='Jones', Id10019='Male', Id10020='Yes', Id10021='1/1/60',
                               Id10022='No', Id10023='1/5/21', instanceid='00'
                               )

    va1.refresh_from_db()
    va2.refresh_from_db()
    va3.refresh_from_db()
    va4.refresh_from_db()

    assert not va1.duplicate
    assert va2.duplicate
    assert va3.duplicate
    assert not va4.duplicate

    va1.Id10022 = 'No'
    va1.save()

    va1.refresh_from_db()
    va2.refresh_from_db()
    va3.refresh_from_db()
    va4.refresh_from_db()

    assert not va1.duplicate
    assert not va2.duplicate
    assert va3.duplicate
    assert va4.duplicate

def test_save_does_not_update_duplicates_without_autodetect_duplicates(settings):
    settings.QUESTIONS_TO_AUTODETECT_DUPLICATES = None

    va1 = VerbalAutopsyFactory.create(Id10017='Bob', Id10018='Jones', Id10019='Male', Id10020='Yes',
                                      Id10021='1/1/60',
                                      Id10022='Yes', Id10023='1/5/21', instanceid='00'
                                      )
    va2 = VerbalAutopsyFactory.create(Id10017='Bob', Id10018='Jones', Id10019='Male', Id10020='Yes',
                                      Id10021='1/1/60',
                                      Id10022='Yes', Id10023='1/5/21', instanceid='00'
                                      )

    va1.refresh_from_db()
    va2.refresh_from_db()

    assert not va1.duplicate
    assert not va2.duplicate
