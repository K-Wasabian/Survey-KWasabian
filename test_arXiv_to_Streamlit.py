import streamlit as st
import arxiv
import pandas as pd

# --- 1. 画面の基本設定 ---
st.set_page_config(page_title="論文高速仕分けツール", layout="wide")
st.title("📚 論文高速スクリーニング＆リスト化システム")

# --- 2. 検索パネル（サイドバー） ---
with st.sidebar:
    st.header("🔍 検索条件")
    st.info("💡 コツ: 文章ではなく、短いキーワードを AND で繋いでください。")
    
    # おすすめのデフォルト検索式をセット
    default_query = 'all:""'
    search_query = st.text_input("検索キーワード", value=default_query)
    max_results = st.number_input("取得件数", min_value=10, max_value=200, value=50, step=10)
    filename_query = st.text_input("ファイル名", value=search_query)
    
    search_btn = st.button("検索を実行")

# --- 3. データ取得処理（API制限なし） ---
def fetch_papers(query, limit):
    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=limit,
        sort_by=arxiv.SortCriterion.Relevance # 関連度が高い順
    )
    
    papers = []
    try:
        for r in client.results(search):
            papers.append({
                "Title": r.title,
                "Year": r.published.year,
                "Authors": ", ".join([a.name for a in r.authors]),
                "Abstract": r.summary.replace('\n', ' '), # 改行を消して読みやすく
                "URL": r.pdf_url # すぐ読めるようにPDFのリンクにする
            })
    except Exception as e:
        st.error(f"検索エラー: {e}")
    return papers

# セッション状態の初期化
if "papers_data" not in st.session_state:
    st.session_state.papers_data = []

if search_btn:
    with st.spinner("論文を取得中..."):
        st.session_state.papers_data = fetch_papers(search_query, max_results)
    if st.session_state.papers_data:
        st.success(f"{len(st.session_state.papers_data)}件の論文を取得しました！右側のリストから確認してください。")
    else:
        st.warning("ヒットしませんでした。キーワードを変えてみてください。")

# --- 4. 論文の高速閲覧＆マーキング機能 ---
if st.session_state.papers_data:
    st.markdown("### 📝 検索結果（要約を読んでチェックを入れてください）")
    
    marked_papers = []
    
    # 取得した論文を1つずつアコーディオン（開閉式）で表示
    for i, paper in enumerate(st.session_state.papers_data):
        # タイトルと発行年を見出しにする
        with st.expander(f"📄 [{paper['Year']}] {paper['Title']}"):
            
            # 【機能2】ワンクリック・マーキング
            is_checked = st.checkbox("✅ この論文を保存リストに入れる", key=f"check_{i}")
            if is_checked:
                marked_papers.append(paper)
            
            # 【機能1】要約の即時展開
            st.write(f"**Authors:** {paper['Authors']}")
            st.markdown(f"**【Abstract】**\n> {paper['Abstract']}")
            st.write(f"[🔗 PDFを開く]({paper['URL']})")

    # --- 5. CSVダウンロード機能 ---
    st.markdown("---")
    st.subheader(f"現在ストックした論文: {len(marked_papers)} 件")
    
    if marked_papers:
        # 【機能3】自動リスト化
        df = pd.DataFrame(marked_papers)
        csv_data = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        
        st.download_button(
            label="📥 チェックした論文をCSVでダウンロード",
            data=csv_data,
            file_name=str(filename_query) + ".csv",
            mime="text/csv"
        )