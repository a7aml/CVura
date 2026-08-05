// Copied from node_modules/plasmo/templates/plasmo.d.ts — Plasmo's own
// ambient module declarations for its import schemes (data-text:, url:,
// etc). Normally scaffolded by `plasmo init`; added by hand here since this
// project's tsconfig didn't have it yet and contents/widget.tsx is the first
// file to use `data-text:` imports.

declare namespace NodeJS {
  interface ProcessEnv {
    NODE_ENV: "development" | "production"

    PLASMO_BROWSER?:
      | "arc"
      | "brave"
      | "chrome"
      | "chromium"
      | "edge"
      | "firefox"
      | "gecko"
      | "island"
      | "opera"
      | "plasmo"
      | "safari"
      | "sigmaos"
      | "tor"
      | "vivaldi"
      | "waterfox"
      | "yandex"

    PLASMO_MANIFEST_VERSION?: "mv2" | "mv3"

    PLASMO_TARGET?: `${ProcessEnv["PLASMO_BROWSER"]}-${ProcessEnv["PLASMO_MANIFEST_VERSION"]}`

    PLASMO_TAG?: string
  }
}

declare module "*.module.css"
declare module "*.module.less"
declare module "*.module.scss"
declare module "*.module.sass"
declare module "*.module.styl"
declare module "*.module.pcss"

declare module "react:*.svg" {
  import type { FunctionComponent, SVGProps } from "react"

  const value: FunctionComponent<SVGProps<SVGSVGElement>>
  export default value
}

declare module "*.gql"
declare module "*.graphql"

declare module "react:*"

declare module "https:*"

declare module "url:*" {
  const value: string
  export default value
}

declare module "data-text:*" {
  const value: string
  export default value
}

declare module "data-base64:*" {
  const value: string
  export default value
}

declare module "data-env:*" {
  const value: string
  export default value
}

declare module "data-text-env:*" {
  const value: string
  export default value
}

declare module "raw:*" {
  const value: string
  export default value
}

declare module "raw-env:*" {
  const value: string
  export default value
}
