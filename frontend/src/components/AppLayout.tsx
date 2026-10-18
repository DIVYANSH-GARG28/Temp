import { NavLink, Outlet } from "react-router-dom";
import {
  Bell,
  Compass,
  GraduationCap,
  LayoutDashboard,
  LogOut,
  Menu,
  Search,
  UserRound,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { ApiError, api, hasAccessToken } from "../services/api";
import type { CurrentUser } from "../types/api";

const navigation = [
  { label: "Dashboard", to: "/dashboard", icon: LayoutDashboard },
  { label: "Discover mentors", to: "/mentors", icon: Compass },
];

export function AppLayout() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [authenticated, setAuthenticated] = useState(hasAccessToken);
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null);
  const [logoutError, setLogoutError] = useState("");
  const navigate = useNavigate();
  const location = useLocation();
  const searchInput = useRef<HTMLInputElement>(null);
  const pageTitle =
    location.pathname === "/dashboard"
      ? "Dashboard"
      : location.pathname === "/mentors"
        ? "Discover mentors"
        : "ConnectED";

  useEffect(() => {
    if (!authenticated) return;
    let active = true;
    void api.getCurrentUser().then(
      (user) => {
        if (active) setCurrentUser(user);
      },
      () => {
        if (active) setCurrentUser(null);
      },
    );
    return () => {
      active = false;
    };
  }, [authenticated]);

  useEffect(() => {
    function focusSearch(event: KeyboardEvent) {
      if (
        event.key === "/" &&
        !event.ctrlKey &&
        !event.metaKey &&
        !event.altKey &&
        !(event.target instanceof HTMLInputElement) &&
        !(event.target instanceof HTMLTextAreaElement)
      ) {
        event.preventDefault();
        searchInput.current?.focus();
      }
    }

    window.addEventListener("keydown", focusSearch);
    return () => window.removeEventListener("keydown", focusSearch);
  }, []);

  function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const query = search.trim();
    navigate(query ? `/mentors?search=${encodeURIComponent(query)}` : "/mentors");
    setMenuOpen(false);
  }

  async function handleLogout() {
    setLogoutError("");
    try {
      await api.logout();
      setCurrentUser(null);
      setAuthenticated(false);
      navigate("/login", { replace: true });
    } catch (cause) {
      setLogoutError(
        cause instanceof ApiError
          ? `Your session was cleared locally, but the server logout failed: ${cause.message}`
          : "Your session was cleared locally, but the server logout failed.",
      );
      setCurrentUser(null);
      setAuthenticated(false);
      navigate("/login", {
        replace: true,
        state: {
          notice: cause instanceof ApiError
            ? `You were signed out locally, but the server logout failed: ${cause.message}`
            : "You were signed out locally, but the server logout failed.",
        },
      });
    }
  }

  return (
    <div className="app-frame">
      <aside className={`sidebar${menuOpen ? " sidebar-open" : ""}`}>
        <a className="brand" href="/" aria-label="connectED home">
          <span className="brand-mark">
            <GraduationCap size={21} strokeWidth={2.2} />
          </span>
          <span>connect<span className="brand-accent">ED</span></span>
        </a>

        <div className="workspace-label">YOUR WORKSPACE</div>
        <nav className="side-nav" aria-label="Main navigation">
          {navigation.map(({ label, to, icon: Icon }) => (
            <NavLink
              className={({ isActive }) =>
                `nav-link${isActive ? " nav-link-active" : ""}`
              }
              key={label}
              to={to}
              end={to === "/"}
              onClick={() => setMenuOpen(false)}
            >
              <Icon size={18} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="sidebar-note">
            <p>A good conversation can open a new door.</p>
            <span>Start with one thoughtful connection.</span>
          </div>
          {authenticated ? (
            <button className="nav-link sidebar-logout" type="button" onClick={() => void handleLogout()}>
              <LogOut size={17} />
              <span>Log out</span>
            </button>
          ) : (
            <a className="nav-link sidebar-login" href="/login">
              <UserRound size={17} />
              <span>Log in</span>
            </a>
          )}
          <span className="sidebar-version">connectED · Preview</span>
        </div>
      </aside>

      {menuOpen && (
        <button
          className="mobile-scrim"
          aria-label="Close navigation"
          onClick={() => setMenuOpen(false)}
        />
      )}

      <div className="main-column">
        <header className="topbar">
          <button
            aria-label={menuOpen ? "Close menu" : "Open menu"}
            aria-expanded={menuOpen}
            className="icon-button mobile-menu"
            onClick={() => setMenuOpen((open) => !open)}
          >
            <Menu size={20} />
          </button>
          <div className="breadcrumb">
            <span>Workspace</span>
            <span className="breadcrumb-divider">/</span>
            <strong>{pageTitle}</strong>
          </div>
          <div className="topbar-right">
            <form className="topbar-search" role="search" onSubmit={submitSearch}>
              <Search size={15} aria-hidden="true" />
              <input
                ref={searchInput}
                aria-label="Search mentors"
                placeholder="Search mentors"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
              />
              <kbd>/</kbd>
            </form>
            <button
              className="icon-button topbar-unavailable"
              type="button"
              title="Notifications are not yet connected"
              aria-label="Notifications unavailable"
              disabled
            >
              <Bell size={16} />
            </button>
            <span className="topbar-divider" />
            <button
              className="profile-control"
              type="button"
              title="View and edit your profile"
              aria-label="View your profile"
              onClick={() => navigate("/dashboard#profile")}
            >
              <span className="avatar avatar-small">
                {currentUser?.name?.trim()
                  ? currentUser.name.trim().split(/\s+/).slice(0, 2).map((part) => part[0]?.toUpperCase()).join("")
                  : <UserRound size={15} />}
              </span>
            </button>
          </div>
        </header>

        {logoutError && (
          <div className="layout-session-notice" role="status">
            {logoutError}
          </div>
        )}
        <main className="page-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
