import pandas as pd
import streamlit as st

from src.models import Article, SearchResult
from src.openalex import search_oql, search_semantic


# -------------------------------------------------------------------------
# Page configuration
# -------------------------------------------------------------------------

st.set_page_config(
    page_title="OpenAlex Search",
    page_icon="📚",
    layout="wide",
)


# -------------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------------


def articles_to_dataframe(articles: list[Article]) -> pd.DataFrame:
    """Convert articles to a flat DataFrame suitable for CSV export."""

    return pd.DataFrame(
        [
            {
                "title": article.title,
                "year": article.year,
                "authors": article.authors_text,
                "source": article.source,
                "doi": article.doi,
                "openalex_id": article.openalex_id,
                "pdf_url": article.pdf_url,
                "cited_by": article.cited_by,
                "concepts": article.concepts,
                "abstract": article.abstract,
            }
            for article in articles
        ]
    )


def display_article(article: Article) -> None:
    """Render a single article."""

    st.subheader(article.title)

    metadata = []

    if article.year:
        metadata.append(str(article.year))

    if article.source:
        metadata.append(article.source)

    metadata.append(f"{article.cited_by} citations")

    st.caption(" · ".join(metadata))

    if article.authors:
        st.write(article.authors_text)

    if article.abstract:
        with st.expander("Abstract"):
            st.write(article.abstract)

    if article.concepts:
        with st.expander("Concepts"):
            st.write(article.concepts)

    links = []

    if article.doi:
        links.append(f"[DOI]({article.doi})")

    if article.openalex_id:
        links.append(f"[OpenAlex]({article.openalex_id})")

    if article.pdf_url:
        links.append(f"[PDF]({article.pdf_url})")

    if links:
        st.markdown(" · ".join(links))

    st.divider()


# -------------------------------------------------------------------------
# Header
# -------------------------------------------------------------------------

st.title("📚 OpenAlex Search")


# -------------------------------------------------------------------------
# Search form
# -------------------------------------------------------------------------

with st.form("search_form"):

    search_mode = st.radio(
        "Search mode",
        options=["Semantic", "Smart / OQL"],
        horizontal=True,
        help=(
            "Semantic searches by meaning. "
            "Smart / OQL lets you write structured OpenAlex queries."
        ),
    )

    if search_mode == "Semantic":

        query = st.text_area(
            "What literature are you looking for?",
            placeholder=(
                "e.g. Infectious disease modelling using "
                "machine learning methods"
            ),
            height=120,
        )

    else:

        query = st.text_area(
            "OQL query",
            placeholder=(
                "e.g. get works since 2022 "
                "about (infectious AND disease)"
            ),
            height=120,
            help=(
                "Use OpenAlex Query Language (OQL), for example: "
                "'get works since 2022 about (cholera AND forecasting)'"
            ),
        )

    # ---------------------------------------------------------------------
    # Advanced filters
    # ---------------------------------------------------------------------

    with st.expander("Advanced filters"):

        col1, col2, col3 = st.columns(3)

        with col1:
            year_from = st.number_input(
                "From year",
                min_value=1900,
                max_value=2100,
                value=2020,
                step=1,
                disabled=(search_mode == "Smart / OQL"),
                help=(
                    "For Smart / OQL searches, include the year "
                    "directly in the OQL query."
                ),
            )

        with col2:
            year_to = st.number_input(
                "To year",
                min_value=1900,
                max_value=2100,
                value=2026,
                step=1,
                disabled=(search_mode == "Smart / OQL"),
                help=(
                    "For Smart / OQL searches, include the year "
                    "directly in the OQL query."
                ),
            )

        with col3:
            result_limit = st.selectbox(
                "Results",
                options=[10, 25, 50],
                index=1,
            )

        # Semantic-specific filters
        if search_mode == "Semantic":

            languages = st.multiselect(
                "Languages",
                options=["English", "French"],
                default=["English", "French"],
                help="Restrict results to selected languages.",
            )

            col4, col5, col6 = st.columns(3)

            with col4:
                open_access_only = st.checkbox(
                    "Open access only",
                    value=False,
                )

            with col5:
                has_abstract = st.checkbox(
                    "Has abstract",
                    value=True,
                )

            with col6:
                include_retracted = st.checkbox(
                    "Include retracted articles",
                    value=False,
                )

            rerank = False

        # OQL-specific options
        else:

            rerank = st.checkbox(
                "Rerank results",
                value=False,
                help=(
                    "Ask OpenAlex to rerank the top relevance results. "
                    "This uses additional API credits."
                ),
            )

            languages = []
            open_access_only = False
            has_abstract = False
            include_retracted = False

    submitted = st.form_submit_button(
        "Search",
        type="primary",
        use_container_width=True,
    )


# -------------------------------------------------------------------------
# Search execution
# -------------------------------------------------------------------------

if submitted:

    if not query.strip():

        st.warning("Enter a search query.")

    elif (
        search_mode == "Semantic"
        and year_from > year_to
    ):

        st.warning("'From year' must be earlier than 'To year'.")

    else:

        try:

            with st.spinner("Searching OpenAlex..."):

                # ---------------------------------------------------------
                # Semantic Search
                # ---------------------------------------------------------

                if search_mode == "Semantic":

                    language_codes = {
                        "English": "en",
                        "French": "fr",
                    }

                    selected_languages = [
                        language_codes[language]
                        for language in languages
                    ]

                    result = search_semantic(
                        query=query,
                        year_from=year_from,
                        year_to=year_to,
                        per_page=result_limit,
                        languages=selected_languages,
                        open_access_only=open_access_only,
                        has_abstract=has_abstract,
                        include_retracted=include_retracted,
                    )

                # ---------------------------------------------------------
                # Smart / OQL
                # ---------------------------------------------------------

                else:

                    result = search_oql(
                        query=query,
                        per_page=result_limit,
                        rerank=rerank,
                    )

            # Keep results alive across Streamlit reruns
            st.session_state["search_result"] = result
            st.session_state["search_mode_used"] = search_mode
            st.session_state["query_used"] = query

        except Exception as exc:

            st.error("OpenAlex could not complete the search.")

            with st.expander("Technical details"):
                st.code(str(exc))


# -------------------------------------------------------------------------
# Results
# -------------------------------------------------------------------------

result: SearchResult | None = st.session_state.get(
    "search_result"
)

if result:

    st.markdown("---")

    st.subheader("Results")

    mode_used = st.session_state.get(
        "search_mode_used",
        "",
    )

    query_used = st.session_state.get(
        "query_used",
        "",
    )

    if query_used:
        st.caption(f'Search: "{query_used}"')

    if mode_used == "Semantic":

        st.caption(
            f"{len(result):,} results returned"
        )

    else:

        st.caption(
            f"{len(result):,} results shown · "
            f"{result.total_count:,} matching works"
        )

    # ---------------------------------------------------------------------
    # Article cards
    # ---------------------------------------------------------------------

    for article in result:
        display_article(article)

    # ---------------------------------------------------------------------
    # CSV export
    # ---------------------------------------------------------------------

    df = articles_to_dataframe(
        result.articles
    )

    csv = df.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        label="Download results as CSV",
        data=csv,
        file_name="openalex_results.csv",
        mime="text/csv",
        use_container_width=True,
    )