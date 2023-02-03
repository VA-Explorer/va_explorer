import csv

from django.http import HttpResponse


def download_queryset_as_csv(queryset, filename, location):
    # Set the response details
    response = csv_response_with_redirect(filename, location)

    model = queryset.model
    model_fields = model._meta.fields + model._meta.many_to_many
    field_names = [field.name for field in model_fields]

    writer = csv.writer(response, delimiter=",")
    # Write the header information
    writer.writerow(field_names)
    # Write the data rows
    for row in queryset:
        values = []
        for field in field_names:
            value = getattr(row, field)
            if callable(value):
                try:
                    value = value() or ""
                except Exception as err:
                    value = f"Error retrieving value: {err}"
            if value is None:
                value = ""
            values.append(value)
        writer.writerow(values)

    return response


def download_list_as_csv(generic_list, filename, location):
    # Set the response details
    response = csv_response_with_redirect(filename, location)

    writer = csv.writer(response, delimiter=",")
    for item in generic_list:
        # Note .writerow() requires a sequence ('', (), []) and places each
        # index in its own column of the row, sequentially
        # If your desired string is not an item in a sequence, writerow() will
        # iterate over each letter in your string
        writer.writerow([item])

    return response


def csv_response_with_redirect(filename, location):
    response = HttpResponse(content_type="text/csv")
    response["Location"] = location
    # TODO: This does not currently set the filename
    response["Content-Disposition"] = f'attachment; filename="{filename}.csv"'
    response.status_code = 302

    return response
