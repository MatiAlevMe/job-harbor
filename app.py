"""Job Harbor — Streamlit UI (v1.1, optional)

Run with: streamlit run app.py
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    import streamlit as st
except ImportError:
    st = None


def main():
    if st is None:
        print("Streamlit no está instalado. Corre: pip install streamlit")
        return

    st.set_page_config(
        page_title="Job Harbor",
        page_icon="🦀",
        layout="wide",
    )

    st.title("🦀 Job Harbor")
    st.markdown("Ofertas de empleo tech alineadas a tu perfil profesional")

    from job_harbor import db

    db.init_db()

    col1, col2 = st.columns([3, 1])

    with col2:
        st.subheader("Filtros")
        min_score = st.slider("Score mínimo", 0, 100, 50, 5)

        st.subheader("Ejecutar búsqueda")
        if st.button("🔄 Buscar ahora", use_container_width=True):
            with st.spinner("Buscando y matcheando ofertas..."):
                from job_harbor.main import cmd_run
                from io import StringIO
                import contextlib

                buf = StringIO()
                with contextlib.redirect_stdout(buf):
                    cmd_run(llm=None)
                st.success("Búsqueda completada")
                st.code(buf.getvalue()[:2000])

    with col1:
        st.subheader("Ofertas rankeadas")
        jobs = db.get_matched_jobs(min_score=min_score)

        if not jobs:
            st.info("No hay ofertas. Ejecuta una búsqueda primero.")
            return

        for j in jobs[:20]:
            score_color = "🟢" if j["match_score"] >= 70 else "🟡" if j["match_score"] >= 50 else "🔴"
            with st.container(border=True):
                c1, c2 = st.columns([5, 1])
                with c1:
                    st.markdown(f"**{j['title']}** — {j['company']}")
                    st.caption(f"{j['location']} · {j['source']}")
                    if j["match_reason"]:
                        st.markdown(f"<small>{j['match_reason']}</small>",
                                  unsafe_allow_html=True)
                with c2:
                    st.markdown(f"## {score_color} {j['match_score']:.0f}%")
                if j["url"]:
                    st.markdown(f"[🔗 Postular]({j['url']})", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
