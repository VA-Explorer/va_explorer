from django.core.management import call_command


# Check all template files for errors, throw error if validation fails
def test_validate_templates():
    # use --no-apps to ignore dependency templates
    call_command("validate_templates", "--no-apps")
