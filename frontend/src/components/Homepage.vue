<template>
  <div class="min-h-screen">
    <div class="max-w-7xl mx-auto py-16 px-6 sm:px-8 lg:py-24 lg:px-10 lg:flex lg:items-center lg:justify-between">
      <h2 class="text-4xl font-bold tracking-tight text-gray-900 sm:text-5xl text-center">
        <span class="block bg-gradient-to-b from-gray-500 to-gray-700 text-transparent bg-clip-text">Request Inspector</span>
        <span class="block bg-gradient-to-b from-gray-800 to-gray-700 text-transparent bg-clip-text">Inspect and debug your HTTP requests effortlessly</span>
      </h2>
      <div class="mt-10 lg:mt-0 lg:ml-6 flex justify-center sm:justify-start">
        <a
          href="/inspector/new/"
          class="inline-flex items-center justify-center bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-3 px-6 border border-transparent rounded-md shadow-lg transition duration-300"
        >
          Get Started
        </a>
      </div>
    </div>

    <div class="max-w-7xl mx-auto py-16 px-6 sm:px-8 lg:py-24 lg:px-10">
      <dl class="space-y-12 lg:space-y-0 lg:grid lg:grid-cols-3 lg:gap-12">

        <div class="relative bg-white rounded-lg shadow-lg p-6 flex flex-col items-center">
          <dt class="flex flex-col items-center">
            <div class="flex items-center justify-center h-14 w-14 rounded-full bg-indigo-600 text-white shadow-lg mb-4">
              <font-awesome-icon :icon="['fas', 'folder-tree']" />
            </div>
            <p class="text-lg leading-6 font-semibold text-gray-900 text-center">HTTP Requests</p>
          </dt>
          <dd class="mt-4 text-base text-gray-500 text-center">
            Request Inspector is your go-to tool for inspecting and debugging HTTP requests. It offers an intuitive interface to explore and analyze requests seamlessly.
          </dd>
        </div>

        <div class="relative bg-white rounded-lg shadow-lg p-6 flex flex-col items-center">
          <dt class="flex flex-col items-center">
            <div class="flex items-center justify-center h-14 w-14 rounded-full bg-indigo-600 text-white shadow-lg mb-4">
              <font-awesome-icon :icon="['fas', 'glasses']" />
            </div>
            <p class="text-lg leading-6 font-semibold text-gray-900 text-center">Real-Time Monitoring</p>
          </dt>
          <dd class="mt-4 text-base text-gray-500 text-center">
            Monitor your HTTP requests in real-time. Stay updated with live data and make informed decisions quickly.
          </dd>
        </div>

        <div class="relative bg-white rounded-lg shadow-lg p-6 flex flex-col items-center">
          <dt class="flex flex-col items-center">
            <div class="flex items-center justify-center h-14 w-14 rounded-full bg-indigo-600 text-white shadow-lg mb-4">
              <font-awesome-icon :icon="['far', 'eye']" />
            </div>
            <p class="text-lg leading-6 font-semibold text-gray-900 text-center">Seamless Integration</p>
          </dt>
          <dd class="mt-4 text-base text-gray-500 text-center">
            Easily integrate Request Inspector into your workflow. Compatible with various platforms and tools for a seamless experience.
          </dd>
        </div>

      </dl>
    </div>
  </div>
</template>

