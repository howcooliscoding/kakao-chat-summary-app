import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import anthropic

# Load environment variables
load_dotenv()
claude_api_key = os.environ.get("CLAUDE_API_KEY")

# Initialize Claude API client
claude_client = anthropic.Anthropic(api_key=claude_api_key)

# Set page title
st.set_page_config(page_title="카카오톡 대화 요약")

# Title and description
st.title("카카오톡 대화 요약 서비스")
st.write("카카오톡 대화 CSV 파일을 업로드하면 대화 내용을 요약해드립니다.")


# Instructions for users
st.markdown("""
## 사용 방법
1. 카카오톡 대화 내보내기 기능을 사용하여 CSV 파일로 대화를 저장합니다.
2. 위의 파일 업로더를 사용하여 저장한 CSV 파일을 업로드합니다.
3. 업로드가 완료되면 대화 내용이 표시됩니다.
4. "대화 요약하기" 버튼을 클릭하여 요약을 생성합니다.
5. 생성된 요약을 확인합니다.

주의: CSV 파일의 인코딩이 UTF-8인지 확인해주세요.
""")



# File upload
uploaded_file = st.file_uploader("카카오톡 대화 CSV 파일을 업로드하세요", type="csv")

if uploaded_file is not None:
    # Read CSV file
    df = pd.read_csv(uploaded_file, encoding='utf-8')


    # 날짜 컬럼을 datetime 형식으로 변환
    df['Date'] = pd.to_datetime(df['Date'])
    
    # '오픈채팅봇'과 '들어왔습니다.'가 포함된 메시지를 필터링
    filtered_df = df[(df['User'] != '오픈채팅봇') & (~df['Message'].str.contains('들어왔습니다.', na=False))]

    # 최근 1주일 데이터만 필터링
    one_week_ago = datetime.now() - timedelta(days=7)
    recent_df = filtered_df[filtered_df['Date'] > one_week_ago]
    


    # Display raw data
    st.subheader("업로드된 대화 내용")
    # st.dataframe(df) # Display the entire conversation
    st.dataframe(recent_df.head(5))  # 최대 5개 행만 표시


    # Prepare conversation text

    # 최근 1주일 대화 내용 추출
    recent_chat = recent_df['Message'].str.cat(sep='\n')

    # print("Recent Chat:\n", recent_chat)

    conversation = "\n".join([f"{row['Date'].strftime('%Y-%m-%d')} {row['User']}: {row['Message']}" for _, row in recent_df.iterrows()])
    system_propmpt="You are an expert in summarizing conversations.\n"
    system_propmpt+="일(daily) 단위로 최근 1주일 간의 대화의 핵심 내용을 요약 하여 bullet point로 정리 합니다..\n"
    system_propmpt+="주요 링크를 추출하여 정리 합니다.\n"
    system_propmpt+="-Please summarize the conversation in Korean.\n"

    system_propmpt+="Constraints: \n"
    system_propmpt+="-이모티콘은 무시 합니다.\n"
    system_propmpt+="-오픈채팅봇은 무시 합니다.\n"
    
    system_propmpt+="Output Example:\n"
    system_propmpt+="## 2024-06-20 대화 요약\n"
    system_propmpt+="### 대화 요약\n"
    system_propmpt+="- ..\n"
    system_propmpt+="- ..\n"
    system_propmpt+="## 2024-06-21 대화 요약\n"
    system_propmpt+="### 대화 요약\n"
    system_propmpt+="- ..\n"
    system_propmpt+="- ..\n"
    
    system_propmpt+="## 주요 링크:\n"
    system_propmpt+="- https://.. \n"
    system_propmpt+="- https://.. \n"



    # print(system_propmpt)
    # print(conversation)
    
    
    
    # Create a button to trigger the summary
    if st.button("대화 요약하기"):
        with st.spinner("대화를 요약하고 있습니다..."):
            # Call Claude API for summary
            response = claude_client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=2000,
                temperature=0.2,
                system=system_propmpt,
                messages=[
                    {"role": "user", "content": f"다음 카카오톡 대화를 요약해주세요! Output Example에 맞게 요약 합니다. \n\nconversation:\n {conversation}"}
                ]
            )
            
            # Display summary
            st.subheader("대화 요약")
            st.write(response.content[0].text)
