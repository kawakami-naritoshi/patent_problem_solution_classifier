import streamlit as st
import pandas as pd
import time
from datetime import datetime
import io
import google.generativeai as genai

# ページ設定
st.set_page_config(
    page_title="PatentScope AI",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# レート制限設定（Gemini API制限に準拠）
RATE_LIMIT_DELAY = 2.5  # 秒間隔

# メインヘッダー
st.title("🔬 課題分類・解決手段分類あてはめアプリ")

# 使い方説明
with st.expander("📖 使い方説明", expanded=True):
    st.markdown("### 🎯 課題分類・解決手段分類あてはめアプリについて")
    st.markdown("AI技術を活用した課題分類・解決手段分類あてはめアプリです。膨大な特許データを自動的に課題分類と解決手段分類に整理します。")
    
    st.markdown("### 📋 使用手順")
    st.markdown("""
    1. **Gemini APIキーの設定**  
       左側のサイドバーでGemini APIキーを入力してください。

    2. **分類定義の入力**  
       対象技術分野に応じた課題分類と解決手段分類を定義してください（入力例として家電分野の分類が表示されています）。

    3. **データファイルのアップロード**  
       「要約」列を含むExcel (.xlsx) ファイルをアップロードしてください。

    4. **分類処理の実行**  
       「分類処理開始」ボタンをクリックして、AI分類を実行します。

    5. **結果のダウンロード**  
       処理完了後、結果をExcelファイルとしてダウンロードできます。
    """)
    
    st.markdown("### ⚠️ 注意事項")
    st.markdown("""
    - **分類定義の入力必須**: 表示されている分類は家電分野の例です。対象技術に適した分類定義を入力してください
    - 大量のデータ処理には時間がかかります（レート制限: 2.5秒間隔で処理）
    - アップロードファイルは「要約」列が必須です
    - 処理中はブラウザを閉じないでください
    """)
    
    st.markdown("### 📊 分類定義について")
    st.markdown("""
    - **技術分野別定義の入力**: 現在表示されている分類は家電分野の例です
    - **分野に応じた定義作成**: IT、バイオ、機械、化学など、各技術分野に適した分類定義を入力してください
    - **分類粒度の調整**: プロジェクトの目的に応じて、より細かいまたは大まかな分類に調整してください
    """)
    
    st.markdown("### 📊 対応形式")
    st.markdown("""
    - **入力**: Excel (.xlsx) ファイル
    - **必須列**: 「要約」
    - **出力**: 元データ + 「課題分類」「解決手段分類」列を追加したExcelファイル
    """)

# サイドバー設定
with st.sidebar:
    st.header("⚙️ 設定")
    
    # APIキー入力
    st.subheader("🔑 Gemini API設定")
    api_key = st.text_input(
        "APIキー",
        type="password",
        help="Google AI Studio (https://makersuite.google.com/app/apikey) で取得できます"
    )
    
    if api_key:
        st.success("APIキーが設定されました ✅")
        # APIキー設定
        genai.configure(api_key=api_key)
    else:
        st.warning("APIキーを入力してください")

# メインコンテンツ
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📝 課題分類定義の入力")
    st.caption("対象技術分野に合わせた課題分類を定義してください")
    
    problem_classification = st.text_area(
        "課題分類カテゴリ（例：家電分野）",
        value="""[モータ効率・性能向上] 説明文: 電気モータの効率改善、小型化、コスト削減、高速化、冷却効率向上など、モータ自体の性能向上に関する課題。省エネ化や製品の小型軽量化に貢献する。,
[ユーザビリティ向上] 説明文: ユーザ操作の簡素化、メンテナンス性の向上、アタッチメントの着脱容易性、操作ボタンの配置改善など、ユーザが製品をより快適に使用するための課題。,
[塵埃分離性能向上] 説明文: サイクロン分離器の分離効率向上、フィルタの目詰まり防止、塵埃の再飛散防止など、真空掃除機における塵埃分離性能に関する課題。清浄性能の維持・向上に繋がる。,
[フィルタのメンテナンス性向上] 説明文: フィルタの取り外しやすさ、清掃の容易さ、交換の簡便さなど、フィルタのメンテナンスに関する課題。ユーザの負担軽減と製品の長期使用に貢献する。,
[ヘアケア機器の使いやすさ向上] 説明文: ヘアケア機器のアタッチメントの改良、髪の絡まり防止、支持体の安定性向上など、ヘアケア機器の使いやすさに関する課題。スタイリングの効率化とユーザの満足度向上に繋がる。,
[歯清掃器具の性能向上] 説明文: 歯清掃器具の清掃能力向上、動作流体の制御改善、ノズルからの液だれ防止など、歯清掃器具の性能に関する課題。口腔衛生の向上に貢献する。,
[部品・構造の設計制約軽減] 説明文: 塵埃分離器の設計自由度向上、ラッチ機構の設計制約軽減、PCBの小型化など、製品の設計における制約を減らす課題。製品の多様化や性能向上に繋がる。,
[安全性・信頼性向上] 説明文: 高温環境下での耐久性向上、電気的ノイズの低減、部品の機械的摩耗の抑制など、製品の安全性と信頼性に関する課題。製品の安全な使用と長寿命化に貢献する。,
[吸引性能の改善] 説明文: ノズル形状の最適化、吸引力向上、隙間への対応、ダクトの操作性向上など、真空掃除機の吸引性能に関する課題。清掃効率の向上に繋がる。,
[接続機構の改善] 説明文: 電力ケーブルの回転機構の改良、アタッチメントの確実な接続、モータ保持の安定性など、部品間の接続機構に関する課題。製品の操作性と耐久性向上に貢献する。""",
        height=300,
        help="対象技術分野に適した課題分類を入力してください（現在は家電分野の例が表示されています）",
        key="problem_def"
    )

with col2:
    st.subheader("🔧 解決手段分類定義の入力")
    st.caption("対象技術分野に合わせた解決手段分類を定義してください")
    
    solution_classification = st.text_area(
        "解決手段分類カテゴリ（例：家電分野）",
        value="""[モータ構造の最適化] 説明文: ブラシレスモータのロータ、ステータ、フレームの配置やストラットの追加により、効率的な動力伝達と小型化を実現する。C字型ステータコアの採用や、ステータコアへの突出部追加によるロータ方向への動き抑制も含まれる。,
[流体制御機構の改良] 説明文: ヘアケア機器や歯清掃器具において、流路形状の最適化、バッフルの配置、ベーンの湾曲などにより、流体の流れを効率的に制御し、目的とする効果（乾燥、清掃など）を最大化する。,
[塵埃分離効率の向上] 説明文: サイクロン分離器の多段化、リブの追加、シュラウドスカートの変形機構、羽根車の利用などにより、空気中の塵埃を効率的に分離・収集する。分離された塵埃の排出機構の改良も含む。,
[フィルタリング機構の改善] 説明文: フィルタの配置（モータ前・後）、形状（環状）、係合部材の追加などにより、空気中の微粒子を効率的に除去し、モータの保護や排気の清浄化を図る。取り外し容易な構造も含まれる。,
[熱管理機構の効率化] 説明文: ヒートシンクの筐体外への露出、フィン形状の最適化、冷却空気の導入などにより、モータやヒータの熱を効率的に放散し、過熱を防ぐ。,
[操作性と安全性の向上] 説明文: ハンドルの形状（楕円断面）、ボタン配置の工夫、インターロック機構の追加、回転接続部の採用などにより、ユーザの操作性を向上させ、誤操作や事故を防ぐ。,
[付属品の機能性向上] 説明文: ヘアケア機器の付属品において、空気流出口の形状、ベーンの配置、リブ付き突出部の追加などにより、特定のヘアスタイルを実現したり、断熱効果を高めたりする。,
[ロータ位置検出の高精度化] 説明文: モータ制御において、巻線電流の変化率や電圧比較など複数のスキームを組み合わせることで、ロータの位置を正確に検出し、効率的なモータ制御を実現する。,
[部品点数削減と組立性向上] 説明文: ステータ組立体をフレームに固定する際に、ラグと凹部を利用したり、フィルタグリルを2つの部品から形成したりすることで、部品点数を削減し、組立作業を容易にする。,
[振動・騒音の低減] 説明文: モータ取付要素に柔軟なスリーブを使用したり、ベアリングをOリングでソフトに取り付けたりすることで、モータの振動を吸収し、騒音を低減する。""",
        height=300,
        help="対象技術分野に適した解決手段分類を入力してください（現在は家電分野の例が表示されています）",
        key="solution_def"
    )

# ファイルアップロード
st.subheader("📁 データファイルアップロード")

col_upload1, col_upload2 = st.columns([2, 1])

with col_upload1:
    uploaded_file = st.file_uploader(
        "Excelファイルを選択してください",
        type=['xlsx'],
        help="「要約」列を含むExcelファイル (.xlsx) をアップロードしてください"
    )

with col_upload2:
    if uploaded_file is not None:
        st.success("✅ ファイル準備完了")
        st.info("アップロード済み")
    else:
        st.warning("📋 ファイル待機中")
        st.info("Excelファイルを選択")

if uploaded_file is not None:
    try:
        # ファイル読み込み
        df = pd.read_excel(uploaded_file)
        
        # 「要約」列の確認
        if '要約' not in df.columns:
            st.error("❌ エラー: 必須列が見つかりません")
            st.error("「要約」列が見つかりません。ファイルを確認してください。")
        else:
            st.success("✅ ファイル読み込み完了")
            st.info(f"{len(df)}行のデータが正常に読み込まれました")
            
            # データプレビュー
            with st.expander("📊 データプレビュー", expanded=False):
                st.dataframe(df.head(10), use_container_width=True)
                st.info(f"📋 データ列: {', '.join(df.columns.tolist())}")
            
            # 分類処理実行
            st.subheader("🚀 分類処理を開始")
            
            if st.button("🚀 分類処理開始", type="primary", disabled=not api_key, use_container_width=True):
                if not api_key:
                    st.error("❌ APIキーが必要です")
                    st.error("左側のサイドバーでGemini APIキーを設定してください。")
                else:
                    # 処理開始
                    st.info("⚡ 処理実行中")
                    st.info("分類処理を開始します。しばらくお待ちください...")
                    
                    # プログレスバー
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # ログコンテナ
                    st.subheader("📝 処理ログ")
                    log_container = st.empty()
                    
                    # ログ用リスト
                    processing_logs = []
                    
                    # 分類処理関数
                    def generate_classification(text, classification_def, classification_type):
                        """AI分類処理"""
                        try:
                            model = genai.GenerativeModel('gemini-2.0-flash-lite')
                            
                            if classification_type == "problem":
                                prompt = f"""##Task: Classify the input problem description into one of the problem categories below. You MUST select the most appropriate category from the list. Do not answer "該当するカテゴリはありません" or similar. Output only the category name in Japanese WITHOUT square brackets [].

##Problem Categories: {classification_def}

##Instructions:
1. Read the input description carefully
2. Compare it with ALL categories
3. Select the MOST appropriate category (even if not perfect match)
4. Output ONLY the category name without brackets []
5. Answer in Japanese only

##Input: {text}

##Answer (category name only, no brackets):"""
                            else:
                                prompt = f"""##Task: Classify the input solution description into one of the solution categories below. You MUST select the most appropriate category from the list. Do not answer "該当するカテゴリはありません" or similar. Output only the category name in Japanese WITHOUT square brackets [].

##Solution Categories: {classification_def}

##Instructions:
1. Read the input description carefully
2. Compare it with ALL categories
3. Select the MOST appropriate category (even if not perfect match)
4. Output ONLY the category name without brackets []
5. Answer in Japanese only

##Input: {text}

##Answer (category name only, no brackets):"""
                            
                            response = model.generate_content(
                                prompt,
                                generation_config={
                                    'temperature': 0.1,
                                    'max_output_tokens': 40,
                                    'candidate_count': 1,
                                }
                            )
                            
                            # 回答から括弧を除去
                            result = response.text.strip()
                            # []括弧がある場合は除去
                            if result.startswith('[') and result.endswith(']'):
                                result = result[1:-1]
                            
                            return result
                        except Exception as e:
                            return f"分類エラー: {str(e)}"
                    
                    try:
                        # 処理時間の推定
                        total_items = len(df)
                        estimated_time = total_items * RATE_LIMIT_DELAY * 2 / 60  # 2回の分類処理
                        
                        processing_logs.append(f"📊 処理対象: {total_items}件")
                        processing_logs.append(f"⏱️ 推定処理時間: 約{estimated_time:.1f}分")
                        
                        # 結果格納用の列を追加
                        df['課題分類'] = ""
                        df['解決手段分類'] = ""
                        
                        start_time = datetime.now()
                        
                        # 課題分類処理
                        processing_logs.append("🎯 課題分類を開始...")
                        log_container.text_area("処理ログ", "\n".join(processing_logs), height=150)
                        
                        for i, row in df.iterrows():
                            # プログレス更新
                            progress = (i / total_items) * 0.5  # 前半50%
                            progress_bar.progress(progress)
                            status_text.text(f"課題分類中... ({i+1}/{total_items})")
                            
                            # 課題分類
                            p_class = generate_classification(
                                row['要約'], 
                                problem_classification, 
                                "problem"
                            )
                            df.at[i, '課題分類'] = p_class
                            
                            processing_logs.append(f"  {i+1}: {p_class}")
                            if i % 5 == 0:  # 5件ごとにログ更新
                                log_container.text_area("処理ログ", "\n".join(processing_logs[-20:]), height=150)
                            
                            # レート制限
                            if i < total_items - 1:
                                time.sleep(RATE_LIMIT_DELAY)
                        
                        # 解決手段分類処理
                        processing_logs.append("🔧 解決手段分類を開始...")
                        log_container.text_area("処理ログ", "\n".join(processing_logs[-20:]), height=150)
                        
                        for i, row in df.iterrows():
                            # プログレス更新
                            progress = 0.5 + (i / total_items) * 0.5  # 後半50%
                            progress_bar.progress(progress)
                            status_text.text(f"解決手段分類中... ({i+1}/{total_items})")
                            
                            # 解決手段分類
                            s_class = generate_classification(
                                row['要約'], 
                                solution_classification, 
                                "solution"
                            )
                            df.at[i, '解決手段分類'] = s_class
                            
                            processing_logs.append(f"  {i+1}: {s_class}")
                            if i % 5 == 0:  # 5件ごとにログ更新
                                log_container.text_area("処理ログ", "\n".join(processing_logs[-20:]), height=150)
                            
                            # レート制限
                            if i < total_items - 1:
                                time.sleep(RATE_LIMIT_DELAY)
                        
                        # 処理完了
                        progress_bar.progress(1.0)
                        end_time = datetime.now()
                        processing_time = (end_time - start_time).total_seconds() / 60
                        
                        status_text.success(f"✅ 分類処理完了！ (実際の処理時間: {processing_time:.1f}分)")
                        processing_logs.append(f"🎉 全ての処理が完了しました！")
                        log_container.text_area("処理ログ", "\n".join(processing_logs[-20:]), height=150)
                        
                        # 結果表示
                        st.header("📊 分類結果")
                        
                        # 統計情報
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader("🎯 課題分類の分布")
                            p_class_counts = df['課題分類'].value_counts()
                            st.bar_chart(p_class_counts)
                            st.dataframe(p_class_counts.to_frame("件数"))
                        
                        with col2:
                            st.subheader("🔧 解決手段分類の分布")
                            s_class_counts = df['解決手段分類'].value_counts()
                            st.bar_chart(s_class_counts)
                            st.dataframe(s_class_counts.to_frame("件数"))
                        
                        # 結果データ表示
                        st.subheader("📋 分類結果詳細")
                        st.dataframe(df[['要約', '課題分類', '解決手段分類']], use_container_width=True)
                        
                        # Excelファイルとしてダウンロード
                        st.subheader("💾 結果ダウンロード")
                        
                        output_buffer = io.BytesIO()
                        with pd.ExcelWriter(output_buffer, engine='openpyxl') as writer:
                            df.to_excel(writer, index=False, sheet_name='分類結果')
                        
                        col_dl1, col_dl2 = st.columns(2)
                        
                        with col_dl1:
                            st.download_button(
                                label="📥 Excelファイルでダウンロード",
                                data=output_buffer.getvalue(),
                                file_name=f"classification_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True
                            )
                        
                        # CSV版ダウンロード
                        csv_buffer = io.StringIO()
                        df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
                        
                        with col_dl2:
                            st.download_button(
                                label="📥 CSVファイルでダウンロード",
                                data=csv_buffer.getvalue(),
                                file_name=f"classification_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv",
                                use_container_width=True
                            )
                        
                    except Exception as e:
                        st.error("❌ 処理エラーが発生しました")
                        st.error(f"{str(e)}")
                        processing_logs.append(f"❌ エラー: {str(e)}")
                        log_container.text_area("処理ログ", "\n".join(processing_logs[-20:]), height=150)
                        
    except Exception as e:
        st.error("❌ ファイル読み込みエラー")
        st.error(f"{str(e)}")

# フッター
st.markdown("---")
st.markdown("### 🔬 課題分類・解決手段分類あてはめアプリ")
st.markdown("**Powered by Gemini Intelligence | 次世代特許分析プラットフォーム**")
st.markdown("Kawakami©2025")
st.info("⚠️ このシステムを使用する際は、対象技術に適した分類定義の入力とGemini APIの利用規約を確認してください")
