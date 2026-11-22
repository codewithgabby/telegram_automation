
import { useEffect, useState } from "react";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const TELEGRAM_USERNAME = "codewithgabby";
const CALENDLY_URL =
  "https://calendly.com/johnfem4real/strategy-session";

type BookingDetails = {
  booking_reference: string;
  package_name: string;
  amount_ngn: number;
  session_count: number;
  status: string;
};

type BankDetails = {
  bank_name: string;
  account_name: string;
  account_number: string;
};

function formatPrice(amount: number) {
  return `₦${Number(amount).toLocaleString("en-NG")}`;
}

function getErrorMessage(data: any, fallback: string) {
  if (typeof data?.detail === "string") return data.detail;
  if (typeof data?.message === "string") return data.message;
  return fallback;
}

export default function ContinuePage() {
  const [booking, setBooking] =
    useState<BookingDetails | null>(null);

  const [bankDetails, setBankDetails] =
    useState<BankDetails | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [bankError, setBankError] = useState("");

  async function readJson(response: Response) {
    return response.json().catch(() => ({}));
  }

  useEffect(() => {
    let cancelled = false;

    async function initialize() {
      const token = new URLSearchParams(
        window.location.hash.slice(1)
      ).get("token");

      if (!token) {
        setError(
          "Your booking link is incomplete. Please open the original booking link."
        );
        setLoading(false);
        return;
      }

      try {
        const [bookingResponse, siteResponse] =
          await Promise.all([
            fetch(
              `${API_BASE_URL}/api/strategy/bookings/continue`,
              {
                method: "POST",
                headers: {
                  "Content-Type": "application/json",
                },
                body: JSON.stringify({ token }),
              }
            ),
            fetch(`${API_BASE_URL}/api/strategy/site`),
          ]);

        const bookingData = await readJson(bookingResponse);
        const siteData = await readJson(siteResponse);

        if (!bookingResponse.ok) {
          throw new Error(
            getErrorMessage(
              bookingData,
              "We could not retrieve your booking."
            )
          );
        }

        if (!cancelled) {
          setBooking(bookingData);

          if (siteResponse.ok) {
            setBankDetails(
              siteData.settings?.payment_bank_details || null
            );

            if (!siteData.settings?.payment_bank_details) {
              setBankError(
                "Payment details are currently unavailable. Please contact Gabriel."
              );
            }
          } else {
            setBankError(
              "Unable to retrieve bank payment details."
            );
          }
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : "Something went wrong. Please try again."
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    initialize();

    return () => {
      cancelled = true;
    };
  }, []);

  function notifyTelegram() {
    if (!booking) return;

    const message = [
      "Hello Gabriel, I have made payment for my Strategy Session.",
      "",
      `Booking reference: ${booking.booking_reference}`,
      `Package: ${booking.package_name}`,
      `Amount paid: ${formatPrice(booking.amount_ngn)}`,
      `Number of sessions: ${booking.session_count}`,
      "",
      "Please kindly verify my payment. Thank you.",
    ].join("\n");

    const telegramUrl =
      `https://t.me/${TELEGRAM_USERNAME}?text=${encodeURIComponent(message)}`;

    window.open(telegramUrl, "_blank", "noopener,noreferrer");
  }

  const paymentApproved =
    booking?.status === "payment_approved";

  return (
    <main style={styles.page}>
      <section style={styles.card}>
        <div style={styles.brand}>GABRIEL JOHNSON</div>

        <h1 style={styles.heading}>Complete your booking</h1>

        <p style={styles.subtitle}>
          Your Personalized Immigration Strategy Session
        </p>

        {loading && (
          <p style={styles.muted}>
            Securely retrieving your booking...
          </p>
        )}

        {!loading && error && (
          <div style={styles.error}>
            <strong>Booking unavailable</strong>
            <p>{error}</p>
          </div>
        )}

        {!loading && booking && (
          <>
            <div style={styles.section}>
              <h2 style={styles.sectionHeading}>
                Your booking summary
              </h2>

              <div style={styles.summary}>
                <span style={styles.label}>Booking reference</span>
                <strong>{booking.booking_reference}</strong>

                <span style={styles.label}>Selected package</span>
                <strong>{booking.package_name}</strong>

                <span style={styles.label}>Amount payable</span>
                <strong style={styles.amount}>
                  {formatPrice(booking.amount_ngn)}
                </strong>

                <span style={styles.label}>Number of sessions</span>
                <strong>{booking.session_count}</strong>

                <span style={styles.label}>Booking status</span>
                <strong style={styles.status}>
                  {booking.status.replaceAll("_", " ")}
                </strong>
              </div>
            </div>

            {paymentApproved ? (
              <div style={styles.approved}>
                <h2>Payment approved!</h2>

                <p>
                  Thank you. Your payment has been verified.
                  You can now schedule your consultation through
                  Calendly.
                </p>

                <a
                  href={CALENDLY_URL}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={styles.primaryButton}
                >
                  Schedule your strategy session
                </a>

                <p style={styles.note}>
                  Your consultation will take place on Telegram,
                  not WhatsApp.
                </p>
              </div>
            ) : (
              <>
                <div style={styles.section}>
                  <h2 style={styles.sectionHeading}>
                    Payment instructions
                  </h2>

                  <p style={styles.muted}>
                    Please transfer the exact amount below to
                    the Ecobank account.
                  </p>

                  {bankDetails ? (
                    <div style={styles.bankBox}>
                      <div style={styles.bankRow}>
                        <span style={styles.label}>Bank</span>
                        <strong>{bankDetails.bank_name}</strong>
                      </div>

                      <div style={styles.bankRow}>
                        <span style={styles.label}>Account name</span>
                        <strong>{bankDetails.account_name}</strong>
                      </div>

                      <div style={styles.bankRow}>
                        <span style={styles.label}>Account number</span>
                        <strong>{bankDetails.account_number}</strong>
                      </div>

                      <div style={styles.bankRow}>
                        <span style={styles.label}>Amount to transfer</span>
                        <strong style={styles.amount}>
                          {formatPrice(booking.amount_ngn)}
                        </strong>
                      </div>
                    </div>
                  ) : (
                    <div style={styles.error}>
                      {bankError || "Bank details unavailable."}
                    </div>
                  )}

                  <p style={styles.note}>
                    Please ensure that you transfer the exact
                    amount for your selected package.
                  </p>
                </div>

                <div style={styles.section}>
                  <h2 style={styles.sectionHeading}>
                    After making payment
                  </h2>

                  <p style={styles.muted}>
                    Once you have completed the bank transfer,
                    notify Gabriel through your existing Telegram
                    conversation.
                  </p>

                  <button
                    type="button"
                    onClick={notifyTelegram}
                    style={styles.primaryButton}
                  >
                    I HAVE MADE PAYMENT — NOTIFY ON TELEGRAM
                  </button>

                  <p style={styles.note}>
                    Gabriel will manually verify your transfer.
                    Once approved, you will receive your Calendly
                    scheduling link through Telegram.
                  </p>
                </div>
              </>
            )}
          </>
        )}

        <div style={styles.footer}>
          <p>
            Need assistance? Contact Gabriel on Telegram:
          </p>
          <strong>@{TELEGRAM_USERNAME}</strong>
          <p>© {new Date().getFullYear()} Gabriel Johnson</p>
        </div>
      </section>
    </main>
  );
}

const styles: Record<string, React.CSSProperties> = {
  page: {
    minHeight: "100vh",
    background: "#f4f7fb",
    padding: "48px 18px",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    fontFamily: "Arial, sans-serif",
    color: "#17243a",
  },
  card: {
    width: "100%",
    maxWidth: "680px",
    background: "#ffffff",
    borderRadius: "18px",
    padding: "36px",
    boxShadow: "0 12px 40px rgba(20, 40, 70, 0.08)",
  },
  brand: {
    color: "#5574a5",
    fontSize: "13px",
    fontWeight: 700,
    letterSpacing: "1.5px",
  },
  heading: {
    fontSize: "28px",
    marginBottom: "8px",
  },
  subtitle: {
    color: "#64748b",
    marginBottom: "28px",
  },
  section: {
    marginTop: "28px",
  },
  sectionHeading: {
    fontSize: "19px",
    marginBottom: "16px",
  },
  summary: {
    display: "grid",
    gap: "10px",
    padding: "22px",
    background: "#f5f8fc",
    border: "1px solid #e3eaf3",
    borderRadius: "12px",
  },
  label: {
    color: "#64748b",
    fontSize: "13px",
    marginTop: "8px",
  },
  amount: {
    fontSize: "25px",
    color: "#174b91",
  },
  status: {
    textTransform: "capitalize",
  },
  bankBox: {
    padding: "20px",
    border: "1px solid #dce5ef",
    borderRadius: "12px",
    background: "#f8fafc",
  },
  bankRow: {
    display: "flex",
    flexDirection: "column",
    gap: "6px",
    marginBottom: "16px",
    wordBreak: "break-word",
  },
  primaryButton: {
    display: "block",
    width: "100%",
    boxSizing: "border-box",
    padding: "16px",
    border: "none",
    borderRadius: "9px",
    background: "#174b91",
    color: "#ffffff",
    fontWeight: 700,
    fontSize: "14px",
    textAlign: "center",
    textDecoration: "none",
    cursor: "pointer",
  },
  muted: {
    color: "#64748b",
    lineHeight: 1.7,
  },
  note: {
    color: "#64748b",
    fontSize: "13px",
    lineHeight: 1.7,
    marginTop: "14px",
  },
  approved: {
    marginTop: "28px",
    padding: "22px",
    borderRadius: "12px",
    background: "#effaf3",
    border: "1px solid #c8ead2",
    color: "#21643a",
    lineHeight: 1.7,
  },
  error: {
    padding: "16px",
    borderRadius: "10px",
    background: "#fff1f1",
    color: "#a32929",
    lineHeight: 1.6,
  },
  footer: {
    marginTop: "36px",
    paddingTop: "20px",
    borderTop: "1px solid #e5eaf0",
    textAlign: "center",
    color: "#64748b",
    fontSize: "13px",
    lineHeight: 1.7,
  },
};
