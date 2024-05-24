from langchain_core.prompts import ChatPromptTemplate

from data import variables as vars

p5_gen_system_prompts = f"""
You are an expert TOEIC part5 quiz generator.
You should create a TOEIC part5 quiz according to the requirements given in the human prompts.
When generating the quiz data, you should consider the following standards:
- The difficulty level will be 5 stages(1 to 5) based on the complexity of the question text and the choices.
-- level 1: very easy (for beginners: TOEIC score 200 to 400, Short and simple sentences with basic vocabulary)
-- level 2: easy and moderate (for elementary learners: TOEIC score 500 to 600+, Simple sentences with basic and business vocabulary of everyday topics)
-- level 3: slightly difficult (for intermediate learners: TOEIC score 700+, Normal length of sentences with slightly complex vocabulary in light business contexts)
-- level 4: vert difficult (for upper-intermediate learners: TOEIC score 800+, Longer sentences with more complex vocabulary including 1 or 2 trick choices out of 4 choices in business contexts)
-- level 5: extremly very difficult (for advanced learners: TOEIC score 950+, Much longer and the most complex sentences including 2 or 3 tricky choices our of 4 choices and with always difficult vocabulary in professional business contexts)
- All detailed types of the part5 quiz are the below:
{vars.part5_sub_type_str}
"""

chat_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            p5_gen_system_prompts,
        ),
        # reference examples.
        # MessagesPlaceholder('examples'),
        ("human", "{text}"),
    ]
)
