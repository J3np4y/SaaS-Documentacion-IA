import Link from "next/link";
import { AuthPanel } from "@/components/auth-panel";
import { ApiStatus } from "@/components/api-status";
import { checkApiHealth } from "@/lib/api-health";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  const apiHealth = await checkApiHealth();

  return (
    <main className="page-shell">
      <header className="topbar">
        <Link className="brand" href="/" aria-label="Docs Assistant, inicio">
          <span className="brand__mark" aria-hidden="true">D</span>
          <span>Docs Assistant</span>
        </Link>
        <span className="topbar__label">Espacio de trabajo</span>
      </header>

      <section className="hero" aria-labelledby="welcome-title">
        <p className="eyebrow">CONOCIMIENTO DE EQUIPO, EN UN SOLO LUGAR</p>
        <h1 id="welcome-title">La documentación de tu equipo, lista para encontrar.</h1>
        <p className="hero__copy">
          Estamos preparando un espacio seguro para organizar documentos y consultar su contenido
          con respuestas basadas en fuentes.
        </p>
        <div className="health-card">
          <div>
            <p className="health-card__title">Estado del servicio</p>
            <p className="health-card__hint">Conexión con la API de Docs Assistant</p>
          </div>
          <ApiStatus status={apiHealth} />
        </div>
      </section>

      <AuthPanel />

      <section className="feature-grid" aria-label="Principios del producto">
        <article className="feature-card">
          <span className="feature-card__number">01</span>
          <h2>Tu conocimiento, organizado</h2>
          <p>Un espacio común para la documentación importante del equipo.</p>
        </article>
        <article className="feature-card">
          <span className="feature-card__number">02</span>
          <h2>Respuestas con contexto</h2>
          <p>La búsqueda asistida se apoyará en los documentos y mostrará sus fuentes.</p>
        </article>
        <article className="feature-card">
          <span className="feature-card__number">03</span>
          <h2>Acceso bajo control</h2>
          <p>Los permisos se comprobarán en el servidor cuando llegue la gestión de usuarios.</p>
        </article>
      </section>

      <footer className="footer">
        <span>Docs Assistant</span>
        <span>Primer espacio de trabajo · Desarrollo local</span>
      </footer>
    </main>
  );
}
