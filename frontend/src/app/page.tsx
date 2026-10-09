import Image from "next/image";
import Link from "next/link";

import { ApiStatus } from "@/components/api-status";
import { AuthPanel } from "@/components/auth-panel";
import { ThemeToggle } from "@/components/theme-toggle";
import { checkApiHealth } from "@/lib/api-health";

export const dynamic = "force-dynamic";

function SparkleIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" fill="none">
      <path d="m12 2 1.9 6.1L20 10l-6.1 1.9L12 18l-1.9-6.1L4 10l6.1-1.9L12 2Z" />
      <path d="m19 15 .9 2.1L22 18l-2.1.9L19 21l-.9-2.1L16 18l2.1-.9L19 15Z" />
    </svg>
  );
}

function DocumentIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" fill="none">
      <path d="M6.75 3.75h7.5l4.5 4.5v12h-12v-16.5Z" />
      <path d="M14.25 3.75v4.5h4.5M9.75 12h6m-6 3.75h6" />
    </svg>
  );
}

export default async function HomePage() {
  const apiHealth = await checkApiHealth();

  return (
    <main className="site-shell">
      <header className="topbar">
        <Link className="brand" href="/" aria-label="Nexora, inicio">
          <Image
            className="brand__mark brand__mark--light"
            src="/brand/nexora-mark-light.png"
            alt=""
            width={44}
            height={48}
            priority
          />
          <Image
            className="brand__mark brand__mark--dark"
            src="/brand/nexora-mark-dark.png"
            alt=""
            width={44}
            height={48}
            priority
          />
          <span className="brand__name">Nexora</span>
        </Link>
        <nav className="topbar__nav" aria-label="Navegación principal">
          <a href="#espacio">Espacio de trabajo</a>
          <a href="#producto">La plataforma</a>
        </nav>
        <div className="topbar__actions">
          <div className="service-pill">
            <ApiStatus status={apiHealth} />
          </div>
          <ThemeToggle />
        </div>
      </header>

      <section className="hero" id="producto" aria-labelledby="welcome-title">
        <div className="hero__content">
          <p className="eyebrow">
            <span className="eyebrow__spark"><SparkleIcon /></span>
            TU CONOCIMIENTO, CONECTADO
          </p>
          <h1 id="welcome-title">
            Todo lo que tu equipo sabe, <span>al alcance.</span>
          </h1>
          <p className="hero__copy">
            Reúne los documentos de tu equipo y encuentra respuestas claras, siempre conectadas
            con sus fuentes.
          </p>
          <div className="hero__actions">
            <a className="button button--primary hero__cta" href="#espacio">
              Explorar mi espacio
              <span aria-hidden="true">↗</span>
            </a>
            <span className="hero__note">Seguro por diseño · Hecho para equipos</span>
          </div>
          <div className="hero__proof">
            <span className="hero__proof-icon"><DocumentIcon /></span>
            <span><strong>Una fuente de verdad</strong><small>Documentos organizados y respuestas con contexto</small></span>
          </div>
        </div>

        <div className="hero-visual" aria-label="Vista previa de Nexora">
          <div className="hero-visual__glow" />
          <div className="preview-card">
            <div className="preview-card__top">
              <span className="preview-card__dots" aria-hidden="true"><i /><i /><i /></span>
              <span className="preview-card__label">NEXORA WORKSPACE</span>
              <span className="preview-card__live"><i /> EN LÍNEA</span>
            </div>
            <div className="preview-card__body">
              <p className="preview-card__eyebrow">ASISTENTE DE CONOCIMIENTO</p>
              <h2>Hola, ¿qué quieres descubrir?</h2>
              <div className="preview-search">
                <span className="preview-search__icon" aria-hidden="true">⌕</span>
                <span>Pregunta a tus documentos...</span>
                <kbd>↵</kbd>
              </div>
              <div className="preview-card__suggestions">
                <span>Ideas para empezar</span>
                <div><i>✦</i> Resume los últimos acuerdos</div>
                <div><i>⌕</i> Busca una política en tus archivos</div>
              </div>
              <div className="preview-source">
                <span className="preview-source__icon"><DocumentIcon /></span>
                <span><strong>Respuestas con evidencia</strong><small>Cada respuesta te lleva a su fuente</small></span>
                <span className="preview-source__check" aria-hidden="true">✓</span>
              </div>
            </div>
          </div>
          <div className="floating-chip floating-chip--top"><span>✦</span> Con contexto</div>
          <div className="floating-chip floating-chip--bottom"><span className="floating-chip__dot" /> Fuentes verificables</div>
        </div>
      </section>

      <section className="workspace-section" id="espacio" aria-labelledby="workspace-title">
        <div className="section-heading">
          <div>
            <p className="eyebrow">TU EQUIPO, EN UN SOLO LUGAR</p>
            <h2 id="workspace-title">Entra a tu espacio de trabajo</h2>
          </div>
          <p>Crea tu organización o continúa donde lo dejaste.</p>
        </div>
        <AuthPanel />
      </section>

      <section className="principles" aria-label="Lo que puedes hacer con Nexora">
        <article className="principle-card">
          <span className="principle-card__icon principle-card__icon--blue"><DocumentIcon /></span>
          <span className="principle-card__index">01 / ORGANIZA</span>
          <h3>El conocimiento, en orden</h3>
          <p>Conserva los documentos de tu equipo en un espacio privado y organizado.</p>
        </article>
        <article className="principle-card">
          <span className="principle-card__icon principle-card__icon--violet"><SparkleIcon /></span>
          <span className="principle-card__index">02 / ENCUENTRA</span>
          <h3>Respuestas que muestran su origen</h3>
          <p>Pregunta en lenguaje natural y sigue cada respuesta hasta la fuente.</p>
        </article>
        <article className="principle-card">
          <span className="principle-card__icon principle-card__icon--green">✓</span>
          <span className="principle-card__index">03 / CONTROLA</span>
          <h3>Tu espacio, tus permisos</h3>
          <p>La organización y sus roles se validan en el servidor, no en el navegador.</p>
        </article>
      </section>

      <footer className="footer">
        <Link className="footer__brand" href="/">
          <Image
            className="brand__mark brand__mark--light"
            src="/brand/nexora-mark-light.png"
            alt=""
            width={26}
            height={28}
          />
          <Image
            className="brand__mark brand__mark--dark"
            src="/brand/nexora-mark-dark.png"
            alt=""
            width={26}
            height={28}
          />
          <span>Nexora</span>
        </Link>
        <span>Conocimiento de equipo, con fuentes y contexto.</span>
        <span className="footer__learning">Proyecto de aprendizaje · No es un servicio de producción</span>
      </footer>
    </main>
  );
}
