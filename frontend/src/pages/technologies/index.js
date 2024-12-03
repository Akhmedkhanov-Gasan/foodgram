import { Title, Container, Main } from '../../components'
import styles from './styles.module.css'
import MetaTags from 'react-meta-tags'

const Technologies = () => {

  return <Main>
    <MetaTags>
      <title>Технологии</title>
      <meta name="description" content="Фудграм - Технологии" />
      <meta property="og:title" content="Технологии" />
    </MetaTags>

    <Container>
      <h1 className={styles.title}>Технологии</h1>
      <div className={styles.content}>
        <div>

          <h2 className={styles.subtitle}>Ключевые технологии</h2>
          <div className={styles.text}>
            <ul className={styles.techList}>
              <li className={styles.textItem}>
                <strong>Python</strong> — язык программирования, обеспечивающий гибкость и производительность.
              </li>
              <li className={styles.textItem}>
                <strong>Django</strong> — мощный веб-фреймворк, который лёг в основу серверной части.
              </li>
              <li className={styles.textItem}>
                <strong>Django REST Framework</strong> — расширение для создания REST API, которое сделало интеграцию с фронтендом бесшовной.
              </li>
              <li className={styles.textItem}>
                <strong>Djoser</strong> — библиотека для удобного управления регистрацией и аутентификацией пользователей.
              </li>
              <li className={styles.textItem}>
                <strong>PostgreSQL</strong> — надёжная реляционная база данных для хранения рецептов и информации о пользователях.
              </li>
              <li className={styles.textItem}>
                <strong>Docker</strong> — контейнеризация проекта, что позволяет запускать его на любом сервере без лишних настроек.
              </li>
              <li className={styles.textItem}>
                <strong>Nginx</strong> — веб-сервер, который отвечает за балансировку нагрузки и быструю доставку контента.
              </li>
            </ul>
          </div>

          <h2 className={styles.subtitle}>Почему эти технологии?</h2>
          <p className={styles.textItem}>
            Каждая из выбранных технологий была выбрана исходя из своих уникальных преимуществ.
            Вместе они составляют надёжный стек для разработки сложных веб-приложений с высокой доступностью
            и возможностью масштабирования.
          </p>
          <p className={styles.textItem}>
            Благодаря этим инструментам проект получился не только функциональным, но и легко поддерживаемым,
            что открывает широкие перспективы для его дальнейшего развития.
          </p>
        </div>
        {/* Добавление изображения */}
        <div className={styles.imageContainer}>
          <img
            src="/technologies.jpg"
            alt="Технологии проекта"
            className={styles.techImage}
          />
        </div>
      </div>
    </Container>
  </Main>
}

export default Technologies
