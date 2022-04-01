import { Localized, useLocalization } from "@fluent/react";
import type { NextPage } from "next";
import { useEffect } from "react";
import { event as gaEvent } from "react-ga";
import styles from "./profile.module.scss";
import BottomBannerIllustration from "../../../../static/images/woman-couch-left.svg";
import checkIcon from "../../../../static/images/icon-check.svg";
import { Layout } from "../../components/layout/Layout";
import { useProfiles } from "../../hooks/api/profile";
import {
  AliasData,
  getAllAliases,
  getFullAddress,
  useAliases,
} from "../../hooks/api/aliases";
import { useUsers } from "../../hooks/api/user";
import { AliasList } from "../../components/dashboard/aliases/AliasList";
import { ProfileBanners } from "../../components/dashboard/ProfileBanners";
import { LinkButton } from "../../components/Button";
import { useRuntimeData } from "../../hooks/api/runtimeData";
import {
  getPlan,
  getPremiumSubscribeLink,
  isPremiumAvailableInCountry,
} from "../../functions/getPlan";
import { useGaViewPing } from "../../hooks/gaViewPing";
import { trackPurchaseStart } from "../../functions/trackPurchase";
import { PremiumOnboarding } from "../../components/dashboard/PremiumOnboarding";
import { Onboarding } from "../../components/dashboard/Onboarding";
import { getRuntimeConfig } from "../../config";
import { SubdomainIndicator } from "../../components/dashboard/subdomain/SubdomainIndicator";
import { Tips } from "../../components/dashboard/Tips";
import { clearCookie, getCookie } from "../../functions/cookies";
import { toast } from "react-toastify";
import { getLocale } from "../../functions/getLocale";
import { InfoTooltip } from "../../components/InfoTooltip";

const Profile: NextPage = () => {
  const runtimeData = useRuntimeData();
  const profileData = useProfiles();
  const userData = useUsers();
  const aliasData = useAliases();
  const { l10n } = useLocalization();
  const bottomBannerSubscriptionLinkRef = useGaViewPing({
    category: "Purchase Button",
    label: "profile-bottom-promo",
  });

  useEffect(() => {
    // This cookie is set in `trackPurchaseStart()`
    const hasClickedPurchaseCookie = getCookie("clicked-purchase") === "true";
    if (hasClickedPurchaseCookie && profileData.data?.[0].has_premium) {
      gaEvent({
        // This used to be an event set by the server;
        // I kept that name even though it's now generated by the client
        // to ensure reports remain consistent:
        category: "server event",
        action: "fired",
        label: "user_purchased_premium",
      });
      clearCookie("clicked-purchase");
    }
  }, [profileData.data]);

  if (!userData.isValidating && userData.error) {
    document.location.assign(getRuntimeConfig().fxaLoginUrl);
  }

  const profile = profileData.data?.[0];
  const user = userData.data?.[0];
  if (
    !runtimeData.data ||
    !profile ||
    !user ||
    !aliasData.randomAliasData.data ||
    !aliasData.customAliasData.data
  ) {
    // TODO: Show a loading spinner?
    return null;
  }

  const setCustomSubdomain = async (customSubdomain: string) => {
    const response = await profileData.update(profile.id, {
      subdomain: customSubdomain,
    });
    if (!response.ok) {
      toast(
        l10n.getString("error-subdomain-not-available", {
          unavailable_subdomain: customSubdomain,
        }),
        { type: "error" }
      );
    }
  };

  if (
    profile.has_premium &&
    profile.onboarding_state < getRuntimeConfig().maxOnboardingAvailable
  ) {
    const onNextStep = (step: number) => {
      profileData.update(profile.id, {
        onboarding_state: step,
      });
    };

    return (
      <Layout>
        <PremiumOnboarding
          profile={profile}
          onNextStep={onNextStep}
          onPickSubdomain={setCustomSubdomain}
        />
      </Layout>
    );
  }

  const createAlias = async (
    options: { type: "random" } | { type: "custom"; address: string }
  ) => {
    try {
      const response = await aliasData.create(options);
      if (!response.ok) {
        throw new Error(
          "Immediately caught to land in the same code path as failed requests."
        );
      }
    } catch (error) {
      toast(l10n.getString("error-alias-create-failed"), { type: "error" });
    }
  };

  const updateAlias = async (
    alias: AliasData,
    updatedFields: Partial<AliasData>
  ) => {
    try {
      const response = await aliasData.update(alias, updatedFields);
      if (!response.ok) {
        throw new Error(
          "Immediately caught to land in the same code path as failed requests."
        );
      }
    } catch (error) {
      toast(
        l10n.getString("error-alias-update-failed", {
          alias: getFullAddress(alias),
        }),
        { type: "error" }
      );
    }
  };

  const deleteAlias = async (alias: AliasData) => {
    try {
      const response = await aliasData.delete(alias);
      if (!response.ok) {
        throw new Error(
          "Immediately caught to land in the same code path as failed requests."
        );
      }
    } catch (error: unknown) {
      toast(
        l10n.getString("error-alias-delete-failed", {
          alias: getFullAddress(alias),
        }),
        { type: "error" }
      );
    }
  };

  const allAliases = getAllAliases(
    aliasData.randomAliasData.data,
    aliasData.customAliasData.data
  );

  const totalBlockedEmails = allAliases.reduce(
    (count, alias) => count + alias.num_blocked,
    0
  );
  const totalForwardedEmails = allAliases.reduce(
    (count, alias) => count + alias.num_forwarded,
    0
  );

  const subdomainMessage =
    typeof profile.subdomain === "string" ? (
      <>
        {l10n.getString("profile-label-domain")}&nbsp;
        <SubdomainIndicator
          subdomain={profile.subdomain}
          onCreateAlias={(address: string) =>
            createAlias({ type: "custom", address: address })
          }
        />
      </>
    ) : (
      <>
        <a className={styles["open-button"]} href="#mpp-choose-subdomain">
          {l10n.getString("profile-label-create-domain")}
        </a>
        <InfoTooltip
          alt={l10n.getString("profile-label-domain-tooltip-trigger")}
        >
          {l10n.getString("profile-label-domain-tooltip")}
        </InfoTooltip>
      </>
    );

  const numberFormatter = new Intl.NumberFormat(getLocale(l10n), {
    notation: "compact",
    compactDisplay: "short",
  });
  // Non-Premium users have only five aliases, making the stats less insightful,
  // so only show them for Premium users:
  const stats = profile.has_premium ? (
    <section className={styles.header}>
      <div className={styles["header-wrapper"]}>
        <div className={styles["user-details"]}>
          <Localized
            id="profile-label-welcome-html"
            vars={{
              email: user.email,
            }}
            elems={{
              span: <span className={styles.lead} />,
            }}
          >
            <span className={styles.greeting} />
          </Localized>
          <strong className={styles.subdomain}>
            <img src={checkIcon.src} alt="" />
            {subdomainMessage}
          </strong>
        </div>
        <dl className={styles["account-stats"]}>
          <div className={styles.stat}>
            <dt className={styles.label}>
              {l10n.getString("profile-stat-label-aliases-used")}
            </dt>
            <dd className={styles.value}>
              {numberFormatter.format(allAliases.length)}
            </dd>
          </div>
          <div className={styles.stat}>
            <dt className={styles.label}>
              {l10n.getString("profile-stat-label-blocked")}
            </dt>
            <dd className={styles.value}>
              {numberFormatter.format(totalBlockedEmails)}
            </dd>
          </div>
          <div className={styles.stat}>
            <dt className={styles.label}>
              {l10n.getString("profile-stat-label-forwarded")}
            </dt>
            <dd className={styles.value}>
              {numberFormatter.format(totalForwardedEmails)}
            </dd>
          </div>
        </dl>
      </div>
    </section>
  ) : (
    <Localized
      id="profile-label-welcome-html"
      vars={{ email: user.email }}
      elems={{ span: <span /> }}
    >
      <section className={styles["no-premium-header"]} />
    </Localized>
  );

  const bottomPremiumSection =
    profile.has_premium ||
    !isPremiumAvailableInCountry(runtimeData.data) ? null : (
      <section className={styles["bottom-banner"]}>
        <div className={styles["bottom-banner-wrapper"]}>
          <div className={styles["bottom-banner-content"]}>
            <Localized
              id="banner-pack-upgrade-headline-html"
              elems={{ strong: <strong /> }}
            >
              <h3 />
            </Localized>
            <p>{l10n.getString("banner-pack-upgrade-copy")}</p>
            <LinkButton
              href={getPremiumSubscribeLink(runtimeData.data)}
              ref={bottomBannerSubscriptionLinkRef}
              onClick={() =>
                trackPurchaseStart({ label: "profile-bottom-promo" })
              }
            >
              {l10n.getString("banner-pack-upgrade-cta")}
            </LinkButton>
          </div>
          <img src={BottomBannerIllustration.src} alt="" />
        </div>
      </section>
    );

  const banners = (
    <section className={styles["banners-wrapper"]}>
      <ProfileBanners
        profile={profile}
        user={user}
        onCreateSubdomain={setCustomSubdomain}
        runtimeData={runtimeData.data}
      />
    </section>
  );
  const topBanners = allAliases.length > 0 ? banners : null;
  const bottomBanners = allAliases.length === 0 ? banners : null;

  return (
    <>
      <firefox-private-relay-addon-data
        // #profile-main is used by the add-on to look up the API token.
        // TODO: Make it look for this custom element instead.
        id="profile-main"
        data-api-token={profile.api_token}
        data-has-premium={profile.has_premium}
        data-fxa-subscriptions-url={`${runtimeData.data.FXA_ORIGIN}/subscriptions`}
        data-premium-prod-id={runtimeData.data.PREMIUM_PRODUCT_ID}
        data-premium-price-id={
          isPremiumAvailableInCountry(runtimeData.data)
            ? getPlan(runtimeData.data).id
            : undefined
        }
        data-aliases-used-val={allAliases.length}
        data-emails-forwarded-val={totalForwardedEmails}
        data-emails-blocked-val={totalBlockedEmails}
        data-premium-subdomain-set={
          typeof profile.subdomain === "string" ? profile.subdomain : "None"
        }
        data-premium-enabled="True"
      ></firefox-private-relay-addon-data>
      <Layout>
        <main className={styles["profile-wrapper"]}>
          {stats}
          {topBanners}
          <section className={styles["main-wrapper"]}>
            <Onboarding
              aliases={allAliases}
              onCreate={() => createAlias({ type: "random" })}
            />
            <AliasList
              aliases={allAliases}
              onCreate={createAlias}
              onUpdate={updateAlias}
              onDelete={deleteAlias}
              profile={profile}
              user={user}
              runtimeData={runtimeData.data}
            />
            <p className={styles["size-information"]}>
              {l10n.getString("profile-supports-email-forwarding", {
                size: getRuntimeConfig().emailSizeLimitNumber,
                unit: getRuntimeConfig().emailSizeLimitUnit,
              })}
            </p>
          </section>
          {bottomBanners}
          {bottomPremiumSection}
        </main>
        <Tips
          profile={profile}
          customAliases={aliasData.customAliasData.data}
        />
      </Layout>
    </>
  );
};

export default Profile;
