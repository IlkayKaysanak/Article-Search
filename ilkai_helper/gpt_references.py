import openai

openai.api_key = ''

def prompt_references(promt_text):
    try:
        # TODO Promptu best practiceye çevir!!
        prompt = "Aşağıdaki referansları AMA formatına çevir:\n"
        prompt += f"{promt_text}\n"

        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=1500,
            n=1,
            stop=None,
            temperature=0.5,
        )

        prompted_references = response.choices[0].text.strip()
        return prompted_references

    except IndexError:
        print(IndexError)


