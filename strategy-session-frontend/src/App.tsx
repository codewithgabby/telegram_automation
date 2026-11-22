import { useEffect, useState, type FormEvent } from "react";
import "./App.css";

type Package = {
  id: string;
  name: string;
  description: string;
  price: number;
  duration: string;
  sessions: number;
  features: string[];
  featured?: boolean;
};

type ApiService = {
  code: string;
  name: string;
  description: string;
  price_ngn: number;
  duration_minutes: number;
  session_count: number;
  features: string[];
  is_active: boolean;
  display_order: number;
};

type ApiContentSection = {
  id: number;
  section_key: string;
  title: string;
  eyebrow: string | null;
  body: string;
  is_active: boolean;
  display_order: number;
};

type StrategySiteResponse = {
  services: ApiService[];
  sections: ApiContentSection[];
  settings: Record<string, Record<string, unknown>>;
};

type BookingResponse = {
  booking_reference: string;
  package_name: string;
  amount_ngn: number;
  session_count: number;
  status: string;
  continuation_url: string;
  message: string;
};

type CustomerDetails = {
  fullName: string;
  email: string;
  whatsapp: string;
  country: string;
  notes: string;
};

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const countries = [
  "Nigeria",
  "Canada",
  "United States",
  "United Kingdom",
  "Ghana",
  "South Africa",
  "Australia",
  "Germany",
  "France",
  "United Arab Emirates",
  "India",
  "Kenya",
  "Ireland",
  "Other",
];

const emptyDetails: CustomerDetails = {
  fullName: "",
  email: "",
  whatsapp: "",
  country: "",
  notes: "",
};

function formatPrice(price: number) {
  return `₦${price.toLocaleString("en-NG")}`;
}

function App() {
  const [packages, setPackages] = useState<Package[]>([]);
  const [packagesLoading, setPackagesLoading] = useState(true);
  const [packagesError, setPackagesError] = useState("");

  // Public website content loaded from the backend.
  const [contentSections, setContentSections] = useState<
    Record<string, ApiContentSection>
  >({});

  const [siteSettings, setSiteSettings] = useState<
  Record<string, Record<string, unknown>>
>({});

const publicSite = siteSettings.public_site || {};

const getPublicSiteText = (
  key: string,
  fallback: string
): string => {
  const value = publicSite[key];

  return typeof value === "string" && value.trim()
    ? value
    : fallback;
};

  const [selectedPackage, setSelectedPackage] =
    useState<Package | null>(null);

  const [step, setStep] = useState(1);
  const [details, setDetails] =
    useState<CustomerDetails>(emptyDetails);

  const [booking, setBooking] =
    useState<BookingResponse | null>(null);

  const [submitting, setSubmitting] = useState(false);
  const [bookingError, setBookingError] = useState("");

  // Load active consultation packages and public website content.
  useEffect(() => {
    async function loadPackages() {
      try {
        setPackagesLoading(true);
        setPackagesError("");

        const response = await fetch(
          `${API_BASE_URL}/api/strategy/site`
        );

        if (!response.ok) {
          throw new Error(
            "Unable to load consultation packages. Please refresh the page."
          );
        }

        const data: StrategySiteResponse = await response.json();

        const loadedPackages: Package[] = data.services.map(
          (item) => ({
            id: item.code,
            name: item.name,
            description: item.description,
            price: item.price_ngn,
            duration:
              item.session_count === 1
                ? `${item.duration_minutes} minutes`
                : `${item.duration_minutes} minutes each day · ${item.session_count} days`,
            sessions: item.session_count,
            features: item.features,
            featured: item.code === "three",
          })
        );

        // Index content sections by their unique section key.
        const loadedSections: Record<string, ApiContentSection> = {};

        for (const section of data.sections || []) {
          loadedSections[section.section_key] = section;
        }

        setPackages(loadedPackages);
setContentSections(loadedSections);
setSiteSettings(data.settings || {});
      } catch (error) {
        setPackagesError(
          error instanceof Error
            ? error.message
            : "Something went wrong loading packages."
        );
      } finally {
        setPackagesLoading(false);
      }
    }

    loadPackages();
  }, []);

  function updateField(
    field: keyof CustomerDetails,
    value: string
  ) {
    setDetails((previous) => ({
      ...previous,
      [field]: value,
    }));
  }

  // Create a real booking through the FastAPI backend.
  async function submitDetails(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    if (!selectedPackage) {
      setBookingError("Please select a consultation package.");
      return;
    }

    const phone = details.whatsapp.trim();

    if (!/^\+[1-9]\d{7,14}$/.test(phone)) {
      setBookingError(
        "Enter a valid international WhatsApp number, including + and your country code."
      );
      return;
    }

    try {
      setSubmitting(true);
      setBookingError("");

      const response = await fetch(
        `${API_BASE_URL}/api/strategy/bookings`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            full_name: details.fullName,
            email: details.email,
            whatsapp: phone,
            country: details.country,
            package_code: selectedPackage.id,
            case_notes: details.notes || null,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Unable to create your booking. Please try again."
        );
      }

      const bookingData = data as BookingResponse;

      if (!bookingData.continuation_url) {
        throw new Error(
          "Booking created, but the continuation link was not returned."
        );
      }

      const continuationUrl = new URL(
        bookingData.continuation_url,
        window.location.origin
      );

      if (
        continuationUrl.origin !== window.location.origin ||
        continuationUrl.pathname !== "/continue"
      ) {
        throw new Error("Invalid booking continuation link.");
      }

      window.location.assign(continuationUrl.toString());
      return;
    } catch (error) {
      setBookingError(
        error instanceof Error
          ? error.message
          : "Something went wrong. Please try again."
      );
    } finally {
      setSubmitting(false);
    }
  }

  function continueToDetails() {
    if (!selectedPackage) return;

    setBookingError("");
    setStep(2);

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  }

  function backToPackages() {
    setStep(1);
    setBooking(null);
    setBookingError("");

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  }

  return (
    <>
      <header className="topbar">
        <a className="brand" href="/">
          <span className="brand-mark">GJ</span>

          <span className="brand-copy">
            <strong>
              {getPublicSiteText("brand_name", "GABRIEL JOHNSON")}
            </strong>

<small>
  {getPublicSiteText(
    "brand_subtitle",
    "IMMIGRATION STRATEGY SERVICES"
  )}
</small>
          </span>
        </a>

        <div className="top-right">
          <span className="secure-label">
            <span className="status-dot" /> Secure booking
          </span>

          <a
            className="help-link"
            href={getPublicSiteText(
  "support_url",
  "https://t.me/CodewithGabby"
)}
            target="_blank"
            rel="noreferrer"
          >
            Need help?
          </a>
        </div>
      </header>

      <main>
        <section className="intro-wrap">
          <div className="intro-copy">
            <div className="eyebrow">
              <span /> PERSONAL IMMIGRATION CONSULTATION
            </div>

            <h1>
              Make your next
              <br />
              immigration move
              <br />
              <em>with clarity.</em>
            </h1>

            <p className="intro-lead">
              Get practical, personalised immigration guidance
              based on your circumstances, goals and available
              options. Choose a consultation package that works
              for you.
            </p>

            <div className="trust-row">
              <span>
                <b>✓</b> Personalised guidance
              </span>
              <span>
                <b>✓</b> Clear next steps
              </span>
              <span>
                <b>✓</b> Confidential consultation
              </span>
            </div>
          </div>

          <aside className="advisor-card">
            <div className="advisor-top">
              <div className="avatar">GJ</div>

              <div>
                <strong>Gabriel Johnson</strong>
                <small>Immigration Consultant</small>
              </div>

              <span className="verified">✓</span>
            </div>

            <div className="advisor-rule" />

            <div className="advisor-stat">
              <span>Consultation format</span>
              <strong>One-on-one</strong>
            </div>

            <div className="advisor-stat">
              <span>Focus</span>
              <strong>Canadian immigration</strong>
            </div>

            <div className="advisor-stat">
              <span>Booking access</span>
              <strong>Worldwide</strong>
            </div>

            <p className="advisor-note">
              Your consultation is focused on your individual
              profile and immigration objectives.
            </p>
          </aside>
        </section>
                <section className="booking-shell">
          <div className="booking-heading">
            <div>
              <span className="section-kicker">
                STEP 0{step} ·{" "}
                {step === 1
                  ? "CHOOSE YOUR PACKAGE"
                  : "YOUR CONTACT DETAILS"}
              </span>

              <h2>
                {step === 1
                  ? "Select your consultation"
                  : "Tell us about yourself"}
              </h2>

              <p>
                {step === 1
                  ? "Choose the level of guidance that best suits your needs."
                  : "Enter your contact information so we can create your booking."}
              </p>
            </div>

            <div className="step-indicator">
              <span
                className={`step-dot ${
                  step >= 1 ? "active" : ""
                }`}
              >
                1
              </span>

              <span className="step-line" />

              <span
                className={`step-dot ${
                  step >= 2 ? "active" : ""
                }`}
              >
                2
              </span>

              <span className="step-line" />

              <span className="step-dot">3</span>
            </div>
          </div>

          <div className="booking-content">
            <div className="main-panel">
              {step === 1 ? (
                <>
                  {packagesLoading && (
                    <p>Loading consultation packages...</p>
                  )}

                  {packagesError && (
                    <p role="alert">{packagesError}</p>
                  )}

                  {!packagesLoading &&
                    !packagesError &&
                    packages.length === 0 && (
                      <p>
                        No consultation packages are currently
                        available.
                      </p>
                    )}

                  {!packagesLoading &&
                    !packagesError &&
                    packages.length > 0 && (
                      <div className="plan-grid">
                        {packages.map((item) => {
                          const selected =
                            selectedPackage?.id === item.id;

                          return (
                            <article
                              key={item.id}
                              className={`plan-card ${
                                item.featured ? "featured" : ""
                              } ${selected ? "selected" : ""}`}
                            >
                              {item.featured && (
                                <span className="popular">
                                  POPULAR CHOICE
                                </span>
                              )}

                              <div className="plan-head">
                                <span className="plan-label">
                                  {item.sessions}{" "}
                                  {item.sessions === 1
                                    ? "SESSION"
                                    : "SESSIONS"}
                                </span>

                                <span className="plan-time">
                                  {item.duration}
                                </span>
                              </div>

                              <h3>{item.name}</h3>

                              <p className="plan-desc">
                                {item.description}
                              </p>

                              <div className="price">
                                {formatPrice(item.price)}
                              </div>

                              <ul>
                                {item.features.map((feature) => (
                                  <li key={feature}>{feature}</li>
                                ))}
                              </ul>

                              <button
                                type="button"
                                className="select-plan"
                                aria-pressed={selected}
                                onClick={() =>
                                  setSelectedPackage(item)
                                }
                              >
                                {selected
                                  ? "Selected"
                                  : "Choose package"}

                                <span>
                                  {selected ? "✓" : "→"}
                                </span>
                              </button>
                            </article>
                          );
                        })}
                      </div>
                    )}

                  <div className="included-note">
                    <span className="info-icon">i</span>

                    <p>
                      <strong>
                        Every consultation is personalised.
                      </strong>{" "}
                      Your selected package determines the number
                      of one-hour sessions. Your private Calendly 
                      scheduling link will be provided after payment approval.
                    </p>
                  </div>
                </>
              ) : (
                <div className="customer-form-wrap">
                  {booking ? (
                    <div className="details-success">
                      <span className="success-mark">✓</span>

                      <h3>Your booking has been created!</h3>

                      <p>
                        Your booking information has been
                        successfully saved.
                      </p>

                      <div className="booking-result">
                        <p>
                          <strong>Booking reference</strong>
                        </p>

                        <h3>{booking.booking_reference}</h3>

                        <p>
                          <strong>Package</strong>
                        </p>

                        <p>{booking.package_name}</p>

                        <p>
                          <strong>Amount payable</strong>
                        </p>

                        <h3>
                          {formatPrice(booking.amount_ngn)}
                        </h3>

                        <p>
                          <strong>Number of sessions</strong>
                        </p>

                        <p>{booking.session_count}</p>

                        <p>
                          <strong>Booking status</strong>
                        </p>

                        <p>
                          {booking.status.replaceAll("_", " ")}
                        </p>
                      </div>

                      <p>
                        Your booking is awaiting payment. Your
                        bank transfer instructions and a Telegram 
                        payment-notification link are available in the next stage.
                      </p>
                    </div>
                  ) : (
                    <form
                      className="customer-form"
                      onSubmit={submitDetails}
                    >
                      <div className="form-section-title">
                        <h3>Personal information</h3>
                        <p>Fields marked with * are required.</p>
                      </div>

                      <label>
                        Full name *
                        <input
                          type="text"
                          autoComplete="name"
                          placeholder="Enter your full name"
                          value={details.fullName}
                          onChange={(e) =>
                            updateField("fullName", e.target.value)
                          }
                          required
                          minLength={2}
                        />
                      </label>

                      <label>
                        Email address *
                        <input
                          type="email"
                          autoComplete="email"
                          placeholder="you@example.com"
                          value={details.email}
                          onChange={(e) =>
                            updateField("email", e.target.value)
                          }
                          required
                        />
                      </label>

                      <label>
                        WhatsApp number *
                        <input
                          type="tel"
                          autoComplete="tel"
                          placeholder="+2348012345678"
                          value={details.whatsapp}
                          onChange={(e) =>
                            updateField("whatsapp", e.target.value)
                          }
                          pattern="\+[1-9][0-9]{7,14}"
                          title="Use international format, for example +2348012345678"
                          required
                        />

                        <small>
                          Include +, country code and number.
                          Example: +2348012345678
                        </small>
                      </label>

                      <label>
                        Country of residence *
                        <select
                          value={details.country}
                          onChange={(e) =>
                            updateField("country", e.target.value)
                          }
                          required
                        >
                          <option value="">
                            Select your country
                          </option>

                          {countries.map((country) => (
                            <option
                              key={country}
                              value={country}
                            >
                              {country}
                            </option>
                          ))}
                        </select>
                      </label>

                      <label className="full-width">
                        Briefly describe your immigration situation

                        <textarea
                          rows={5}
                          placeholder="Tell us about your current immigration situation, goals or questions (optional)."
                          value={details.notes}
                          onChange={(e) =>
                            updateField("notes", e.target.value)
                          }
                          maxLength={2000}
                        />

                        <small>
                          {details.notes.length}/2000 characters
                        </small>
                      </label>

                      {bookingError && (
                        <p
                          className="booking-error"
                          role="alert"
                        >
                          {bookingError}
                        </p>
                      )}

                      <div className="form-actions full-width">
                        <button
                          type="button"
                          className="back-button"
                          onClick={backToPackages}
                          disabled={submitting}
                        >
                          ← Back to packages
                        </button>

                        <button
                          type="submit"
                          className="continue-button"
                          disabled={submitting}
                        >
                          {submitting
                            ? "Creating booking..."
                            : "Create my booking →"}
                        </button>
                      </div>
                    </form>
                  )}
                </div>
              )}
            </div>

            <aside className="side-panel">
              <div className="side-title">
                <span className="section-kicker">
                  AT A GLANCE
                </span>

                <h3>Your booking</h3>
              </div>

              {selectedPackage ? (
                <div className="side-selection">
                  <strong className="side-plan-name">
                    {selectedPackage.name}
                  </strong>

                  <div className="side-plan-price">
                    {formatPrice(selectedPackage.price)}
                  </div>

                  <p className="side-plan-meta">
                    {selectedPackage.duration}
                  </p>

                  {step === 1 && (
                    <button
                      type="button"
                      className="continue-button side-continue"
                      onClick={continueToDetails}
                    >
                      Continue to details →
                    </button>
                  )}
                </div>
              ) : (
                <div className="empty-selection">
                  <span>↗</span>

                  <strong>No package selected yet</strong>

                  <small>
                    Your selected package and booking summary
                    will appear here.
                  </small>
                </div>
              )}

              <div className="side-divider" />

              <div className="side-assurance">
                <span className="assurance-icon">✓</span>

                <div>
                  <strong>Personal guidance</strong>

                  <p>
                    Focused on your circumstances and practical
                    next steps.
                  </p>
                </div>
              </div>

              <div className="side-assurance">
                <span className="assurance-icon">⌁</span>

                <div>
                  <strong>Manual payment review</strong>

                  <p>
                    Payment is checked before booking access is
                    approved.
                  </p>
                </div>
              </div>

              <div className="side-footer">
                <span>Questions about your booking?</span>

                <a
  href={getPublicSiteText(
    "support_url",
    "https://t.me/CodewithGabby"
  )}
  target="_blank"
  rel="noreferrer"
>
  <strong>
    {getPublicSiteText(
      "contact_label",
      "Contact Gabe directly"
    )}
  </strong>
</a>

                <small>
                  Support information will be provided with your
                  booking.
                </small>
              </div>
            </aside>
          </div>
        </section>

        <section className="bottom-trust">
          <div>
            <span className="trust-icon">✓</span>

            <span>
              <strong>
                {contentSections.confidentiality?.title ||
                  "Confidential by design"}
              </strong>

              <small>
                {contentSections.confidentiality?.body ||
                  "Your consultation details are handled privately."}
              </small>
            </span>
          </div>

          <div>
            <span className="trust-icon">◷</span>

            <span>
              <strong>
                {contentSections.guidance?.title ||
                  "Guidance built around you"}
              </strong>

              <small>
                {contentSections.guidance?.body ||
                  "Practical direction for your next decision."}
              </small>
            </span>
          </div>

          <div>
            <span className="trust-icon">₦</span>

            <span>
              <strong>
                {contentSections.pricing?.title ||
                  "Transparent pricing"}
              </strong>

              <small>
                {contentSections.pricing?.body ||
                  "No hidden consultation fees."}
              </small>
            </span>
          </div>
        </section>
      </main>

      <footer>
        <span>
          © {new Date().getFullYear()}{" "}
{getPublicSiteText("footer_name", "Gabriel Johnson")} ·
{getPublicSiteText(
  "footer_brand",
  "Immigration Strategy Services"
)}
        </span>

        <span>
          {getPublicSiteText(
  "footer_tagline",
  "Canada-focused immigration guidance · Worldwide bookings"
)}
        </span>
      </footer>
    </>
  );
}

export default App;