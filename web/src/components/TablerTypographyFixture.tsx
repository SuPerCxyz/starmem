import fixtureMarkup from "../typography-fixture.html?raw";

/** Internal-only typography fixture. It is not linked from the product shell. */
export function TablerTypographyFixture() {
  return <div dangerouslySetInnerHTML={{ __html: fixtureMarkup }} />;
}
