def to_sentence_case(sentence):
    return sentence.title().replace('-', ' ').replace('_', ' ')


def remove_null_values(json: dict) -> dict:
    result = {}
    for key, value in json.items():
        if value is not None:
            result.update({key: value})

    return result


def to_image_from_json(json: dict) -> list[object]:
    from pyrinth.projects import Project
    return [Project.GalleryImage.from_json(image) for image in json]


def json_to_query_params(json_: dict) -> str:
    import json
    result = ''
    for key, value in json_.items():
        result += f'{key}={json.dumps(value)}&'
    return result


def remove_file_path(file):
    return ''.join(file.split('/')[-1])
