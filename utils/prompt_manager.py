class PromptManager:

    @staticmethod
    def summarize(lang, other_prompt = None):
        return f"""
You are a competent research assistant. I would input a pdf essay / report, and I would like you to summarize that file precisely. 

Detailed instructions:
1. I would like you to output the summary in **{lang}**, please conform with this instruction strictly.
2. The output should be in JSON format.
3. Please summarize in details. All paragraphs should be summarized correctly.
4. The summary should follow the format that I give you. Give me structrual summary data rather than only description.
5. Summary should be a valid string format that does not affect the parsing of JSON. However, the content should be a valid HTML format!
6. Please also recognize and highlight the keywords in your summary, making them bold by <strong> tag.
7. Please also label the source page number by (p. ##) format at the end of all sentences that you consider important.
8. Use relatively easy-to-understand tone, assume that I'm a freshman.

Other instructions:
{other_prompt}

<output schema>
{{"summary": "<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Summary</title>
</head>
<body>

  <h3>Brief Summary</h3>

  <h3>Paragraphs</h3>
  <ul>
    <li>
      <h4>Paragraph 1 Title</h4>
      <p>Paragraph 1 summary</p>
    </li>
    <li>
      <h4>Paragraph 2 Title</h4>
      <p>Paragraph 2 summary</p>
    </li>
    </ul>

  <h3>Implication</h3>

  <h3>Keywords</h3>
  <p>
    #keyword1, #keyword2, #keyword3, ... list 7 - 10 
  </p>

</body>
</html>"}}
"""
    
    @staticmethod
    def chat():
      return """Please be nice to meeee hehehe
      """
      
    
    @staticmethod
    def others():
        return {
            "淺顯易懂的摘要": "**Please make sure that your tone is easily understandable! I'm not that smart.**",
            "著重解釋研究方法": "**Please put more emphasis on the 'research methodology', specifying the detail of hypotheses, merits, and limitation of that methodology. Also remember to plug in the equation if any.**"
        }